#!/usr/bin/env python3

import board
import time
import logging
import threading
import json
import argparse
from adafruit_sgp40 import SGP40
from adafruit_pm25.i2c import PM25_I2C
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from configparser import ConfigParser

class SensorThread( threading.Thread ):

    def __init__( self, i2c ):
        super().__init__()
        self.running = True
        self.daemon = True
        self.pm25 = PM25_I2C( i2c )
        self.sgp40 = SGP40( i2c )
        self.lock = threading.Lock()

    def run( self ):

        logger = logging.getLogger( 'sensors.run' )

        logger.info( 'sensor thread starting...' )

        while self.running:

            new_airq = {}

            try:
                pm25_airq = self.pm25.read()

                # Sanitize pm25 keys.
                for key in pm25_airq:
                    new_key = key.replace( ' ', '_' )
                    new_airq[new_key] = pm25_airq[key]

            except Exception as e:
                logger.error( 'error updating air quality pm25: {}'.format(
                    e ) )

            try:
                new_airq['tvoc'] = self.sgp40.raw

            except Exception as e:
                logger.error( 'error updating air quality tvoc: {}'.format(
                    e ) )

            new_airq['timestamp'] = int( time.time() )

            with self.lock:
                self.airq = new_airq

            logger.debug( 'updating...' )

            time.sleep( 5 )

class SensorHTTPHandler( SimpleHTTPRequestHandler ):

    def do_GET( self ):

        logger = logging.getLogger( 'http.get' )

        self.send_response( 200 )
        self.send_header( 'Content-type', 'text/json' )
        self.end_headers()

        airq = {}
        airq = self.server.sensor_thread.airq
        logger.debug( 'response readings updated {}...'.format(
            airq['timestamp'] ) )
        airq_json = json.dumps( airq )
        self.wfile.write( airq_json.encode( 'utf-8' ) )

    def log_message( self, format, *args ):
        return

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument( '-c', '--config', action='store' )

    parser.add_argument( '-v', '--verbose', action='store_true' )

    args = parser.parse_args()

    level = logging.INFO
    if args.verbose:
        level=logging.DEBUG
    logging.basicConfig( level=level )
    l = logging.getLogger( 'airq' )

    config = ConfigParser()
    config.read( args.config )

    i2c = board.I2C()

    listen = (config['server']['listen'], config.getint( 'server', 'port' ))
    server = ThreadingHTTPServer( listen, SensorHTTPHandler )
    server.sensor_thread = SensorThread( i2c )
    server.sensor_thread.start()
    l.info( 'web server starting...' )
    server.serve_forever()

if '__main__' == __name__:
    main()



import argparse
import configparser
import ssl
import logging
import pymysql
from paho.mqtt import client as mqtt_client
from urllib.parse import urlparse

topics = []
conn = None

def on_connected( client, userdata, flags, rc ):
    logger = logging.getLogger( 'mqtt' )
    logger.info( 'mqtt connected' )
    for topic in topics:
        logger.info( 'subscribing to %s...', topic )
        client.subscribe( topic )

def on_message( client, userdata, msg ):
    with conn:
        with conn.cursor() as cursor:
            sql = 'INSERT INTO `mqtt` (`topic`, `value`) VALUES (%s, %d)'
            cursor.execute( msg.topic, int( msg.payload ) )

def stop( client ):
    logger = logging.getLogger( 'mqtt' )
    logger.info( 'mqtt shutting down...' )
    client.disconnect()
    client.loop_stop()

def client_connect( client, config ):
    logger = logging.getLogger( 'mqtt' )
    client.loop_start()
    client.enable_logger()
    client.tls_set( config['mqtt']['ca'], tls_version=ssl.PROTOCOL_TLSv1_2 )
    client.on_connect = on_connected
    client.on_message = on_message
    logger.info( 'connecting to MQTT at %s:%d...',
        config['mqtt']['host'], config.getint( 'mqtt', 'port' ) )
    client.username_pw_set(
        config['mqtt']['user'], config['mqtt']['password'] )
    client.connect( config['mqtt']['host'], config.getint( 'mqtt', 'port' ) )

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument( '-c', '--config-file', default='/etc/dbfetch_mqtt.ini' )

    args = parser.parse_args()

    logging.basicConfig( level=logging.INFO )
    logger = logging.getLogger( 'main' )

    config = configparser.RawConfigParser()
    config.read( args.config_file )

    db_url = urlparse( config['mqtt']['connection'] )
    conn = pymysql.connect(
        host=db_url.hostname,
        user=db_url.username,
        password=db_url.password,
        database=db_url.path[1:]
    )

    for location in config['mqtt']['locations'].split( ',' ):
        topics.append( config[location]['topic'] )

    client = mqtt_client.Client( config['mqtt']['uid'], True, None, mqtt_client.MQTTv31 )
    client_connect( client, config )

    while True:
        pass

if '__main__' == __name__:
    main()

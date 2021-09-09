
import argparse
import configparser
import ssl
import logging
import pymysql
from paho.mqtt import client as mqtt_client
from urllib.parse import urlparse

topics = []
db_url = None

def on_connected( client, userdata, flags, rc ):
    logger = logging.getLogger( 'mqtt' )
    logger.info( 'mqtt connected' )
    for topic in topics:
        logger.info( 'subscribing to %s...', topic )
        client.subscribe( topic )

def on_message( client, userdata, msg ):
    global db_url
    logger = logging.getLogger( 'mqtt' )
    try:
        logger.debug( 'connecting to %s as %s, database: %s',
            db_url.hostname,
            db_url.username,
            db_url.path[1:] )
        conn = pymysql.connect(
            host=db_url.hostname,
            user=db_url.username,
            password=db_url.password,
            database=db_url.path[1:],
            cursorclass=pymysql.cursors.DictCursor )
        cursor = conn.cursor()
        sql = 'INSERT INTO `mqtt` (`topic`, `value`) VALUES (%s, %s)'
        cursor.execute( sql, (msg.topic, msg.payload ) )
        conn.commit()
        conn.close()
    except Exception as ex:
        logger.exception( ex )

def stop( client ):
    logger = logging.getLogger( 'mqtt' )
    logger.info( 'mqtt shutting down...' )
    client.disconnect()
    client.loop_stop()

def client_connect( client, config, verbose ):
    logger = logging.getLogger( 'mqtt' )
    if verbose:
        client.enable_logger()
    client.tls_set( config['mqtt']['ca'], tls_version=ssl.PROTOCOL_TLSv1_2 )
    client.on_connect = on_connected
    client.on_message = on_message
    logger.debug( 'connecting to MQTT at %s:%d...',
        config['mqtt']['host'], config.getint( 'mqtt', 'port' ) )
    client.username_pw_set(
        config['mqtt']['user'], config['mqtt']['password'] )
    client.connect( config['mqtt']['host'], config.getint( 'mqtt', 'port' ) )

def main():

    global db_url

    parser = argparse.ArgumentParser()

    parser.add_argument( '-c', '--config-file', default='/etc/dbfetch_mqtt.ini' )

    parser.add_argument( '-v', '--verbose' )

    args = parser.parse_args()

    logging.basicConfig( level=logging.DEBUG if args.verbose else logging.INFO )
    logger = logging.getLogger( 'main' )

    config = configparser.RawConfigParser()
    config.read( args.config_file )

    db_url = urlparse( config['mqtt']['connection'] )

    for location in config['mqtt']['locations'].split( ',' ):
        topics.append( config[location]['topic'] )

    client = mqtt_client.Client( config['mqtt']['uid'], True, None, mqtt_client.MQTTv31 )
    client_connect( client, config, args.verbose )
    client.loop_forever()

if '__main__' == __name__:
    main()

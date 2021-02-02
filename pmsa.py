#!/usr/local/bin/python2.7

import argparse
import logging
from sqlalchemy import create_engine
from dbfetch.request import Requester
from ConfigParser import RawConfigParser
from models import PMSA, create_pmsa
from datetime import datetime

parser = argparse.ArgumentParser()

parser.add_argument( '-v', '--verbose', action='store_true' )

args = parser.parse_args()

level = logging.ERROR
if args.verbose:
    level = logging.DEBUG
logging.basicConfig( level=level )
logger = logging.getLogger( 'main' )

config = RawConfigParser()
with open( './pmsa.ini' ) as a:
    res = config.readfp( a )

db = create_engine( config.get( 'global', 'connection' ) )
create_pmsa( db )

locations = config.get( 'global', 'locations' ).split( ',' )
for l in locations:
    logger.debug( 'checking location: {}...'.format( l ) )
    r = Requester( db, {
        'timestamp': lambda o: datetime.fromtimestamp( o ).strftime( '%Y-%m-%dT%H:%M:%S.%f' )
    } )
    r.request( config.get( 'location-{}'.format( l ), 'url' ) )
    for obj in r.format_json():
        obj['location'] = l
        r.store( obj, PMSA, PMSA.timestamp, timestamp=obj['timestamp'] )

    r.commit()


#!/usr/local/bin/python2.7

from sqlalchemy import create_engine
from dbfetch import Requester
from ConfigParser import RawConfigParser
from models import Awair, create_awair

config = RawConfigParser()
with open( '/home/dbfetch/awair.ini' ) as a:
    res = config.readfp( a )

db = create_engine( config.get( 'global', 'connection' ) )
create_awair( db )

locations = config.get( 'global', 'locations' ).split( ',' )
for l in locations:
    r = Requester( db, {
        'timestamp': lambda o: Requester.format_date( o ),
    } )
    r.request( config.get( 'location-{}'.format( l ), 'url' ) )
    for obj in r.format_json():
        obj['location'] = l
        r.store( obj, Awair, Awair.timestamp, timestamp=obj['timestamp'] )

    r.commit()


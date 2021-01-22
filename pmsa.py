#!/usr/local/bin/python2.7

from sqlalchemy import create_engine
from dbfetch import Requester
from ConfigParser import RawConfigParser
from models import PMSA, create_pmsa
from datetime import datetime

config = RawConfigParser()
with open( '/home/dbfetch/pmsa.ini' ) as a:
    res = config.readfp( a )

db = create_engine( config.get( 'global', 'connection' ) )
create_pmsa( db )

locations = config.get( 'global', 'locations' ).split( ',' )
for l in locations:
    r = Requester( db, {
        'timestamp': lambda o: datetime.fromtimestamp( o ).strftime( '%Y-%m-%dT%H:%M:%S.%f' )
    } )
    r.request( config.get( 'location-{}'.format( l ), 'url' ) )
    for obj in r.format_json():
        obj['location'] = l
        r.store( obj, PMSA, PMSA.timestamp, timestamp=obj['timestamp'] )

    r.commit()


#!/usr/local/bin/python2.7

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from dbfetch import Requester
from ConfigParser import RawConfigParser
from models import Awair, create_awair

Base = declarative_base()

config = RawConfigParser()
with open( '/home/dbfetch/awair.ini' ) as a:
    res = config.readfp( a )

db = create_engine( config.get( 'db', 'connection' ) )
create_awair( db )

r = Requester( db, {
    'timestamp': lambda o: Requester.format_date( o ),
} )
r.request( config.get( 'request', 'url' ) )
for obj in r.format_json():
    obj['location'] = config.get( 'request', 'location' )
    r.store( obj, Awair, Awair.timestamp, timestamp=obj['timestamp'] )

r.commit()


#!/usr/local/bin/python2.7

from sqlalchemy import create_engine
from dbfetch import Requester
from ConfigParser import RawConfigParser
from models import COVID, create_covid

config = RawConfigParser()
with open( '/home/dbfetch/covid.ini' ) as a:
    res = config.readfp( a )

db = create_engine( config.get( 'global', 'connection' ) )
create_covid( db )

r = Requester( db, modifiers={
    'test_date': lambda o: Requester.format_date( o ),
} )
r.request( config.get( 'global', 'url' ) )
for obj in r.format_json():
    r.store( obj, COVID, COVID.test_date, test_date=obj['test_date'] )

r.commit()



#!/usr/local/bin/python2.7

from sqlalchemy import create_engine, Column, Integer, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dbfetch import Requester
from ConfigParser import RawConfigParser

Base = declarative_base()

config = RawConfigParser()
with open( '/home/dbfetch/covid.ini' ) as a:
    res = config.readfp( a )

db = create_engine( config.get( 'db', 'connection' ) )

class COVID( Base ):
    __tablename__ = 'covid'
    
    test_date = Column( DateTime, primary_key=True )
    county = Column( String( 32 ) )
    new_positives = Column( Integer )
    cumulative_number_of_positives = Column( Integer )
    total_number_of_tests = Column( Integer )
    cumulative_number_of_tests = Column( Integer )

Base.metadata.create_all( db )

r = Requester( db, modifiers={
    'test_date': lambda o: Requester.format_date( o ),
} )
r.request( config.get( 'request', 'url' ) )
for obj in r.format_json():
    r.store( obj, COVID, COVID.test_date, test_date=obj['test_date'] )

r.commit()



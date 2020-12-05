#!/usr/local/bin/python2.7

from sqlalchemy import create_engine, Column, Integer, DateTime, String, Float, Float
from sqlalchemy.ext.declarative import declarative_base
from dbfetch import Requester
from ConfigParser import RawConfigParser

Base = declarative_base()

config = RawConfigParser()
with open( '/home/dbfetch/awair.ini' ) as a:
    res = config.readfp( a )

db = create_engine( config.get( 'db', 'connection' ) )

class Awair( Base ):
    __tablename__ = 'awair'

    location = Column( Integer, primary_key=True )
    timestamp = Column( DateTime, primary_key=True )
    score = Column( Integer )
    dew_point = Column( Float )
    temp = Column( Float )
    humid = Column( Float )
    abs_humid = Column( Float )
    co2 = Column( Float )
    co2_est = Column( Float )
    voc = Column( Float )
    voc_baseline = Column( Float )
    voc_h2_raw = Column( Float )
    voc_ethanol_raw = Column( Float )
    pm25 = Column( Float )
    pm10_est = Column( Float )

Base.metadata.create_all( db )

r = Requester( db, {
    'timestamp': lambda o: Requester.format_date( o ),
} )
r.request( config.get( 'request', 'url' ) )
for obj in r.format_json():
    obj['location'] = config.get( 'request', 'location' )
    r.store( obj, Awair, Awair.timestamp, timestamp=obj['timestamp'] )

r.commit()


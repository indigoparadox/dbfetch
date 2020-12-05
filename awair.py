#!/usr/local/bin/python2.7

import requests
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, DateTime, String, Float, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

db = create_engine()

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

r = requests.get()
reading = r.json()

reading['location'] = 1
reading['timestamp'] = datetime.strptime( reading['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ' )

Session = sessionmaker()
Session.configure( bind=db )
session = Session()

reading_row = Awair( **reading )
session.add( reading_row )
session.commit()


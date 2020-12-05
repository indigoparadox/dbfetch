#!/usr/local/bin/python2.7

import requests
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

db = create_engine()

class COVID( Base ):
    __tablename__ = 'covid'
    
    test_date = Column( DateTime, primary_key=True )
    county = Column( String( 32 ) )
    new_positives = Column( Integer )
    cumulative_number_of_positives = Column( Integer )
    total_number_of_tests = Column( Integer )
    cumulative_number_of_tests = Column( Integer )

Base.metadata.create_all( db )
Session = sessionmaker()
Session.configure( bind=db )
session = Session()

r = requests.get()

for row in r.json():
    row['test_date'] = datetime.strptime( row['test_date'], '%Y-%m-%dT%H:%M:%S.%f' )

    if not session.query( COVID.test_date ).filter_by( test_date=row['test_date'] ).scalar():
        db_row = COVID( **row )
        session.add( db_row )

session.commit()



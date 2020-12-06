#!/usr/local/bin/python2.7

from dbfetch import Plotter
from datetime import timedelta, datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ConfigParser import RawConfigParser
from models import COVID, create_covid
from matplotlib.dates import HourLocator, DateFormatter, DayLocator, MonthLocator
import os

config = RawConfigParser()
with open( '/home/dbfetch/covid.ini' ) as a:
    res = config.readfp( a )

db = create_engine( config.get( 'global', 'connection' ) )
create_covid( db )

Session = sessionmaker()    
Session.configure( bind=db )
session = Session()

now = datetime.now()

indexes = {
    'new_positives': {
        'field': COVID.new_positives,
        'label': 'New Positives',
    },
    'total_number_of_tests': {
        'field': COVID.total_number_of_tests,
        'label': 'Total Tests',
    },
}

intervals = Plotter.intervals( now )
for t in intervals:
    p = Plotter(
        'COVID New Positives', intervals[t]['locator'], intervals[t]['formatter'],
        w=intervals[t]['width'] )

    for i in indexes:
        times = []
        data = []
        for row in session.query( COVID.test_date, indexes[i]['field'] ) \
        .filter( COVID.test_date >= intervals[t]['start'] ):
            # Timezone intervention.
            times.append( row[0] - timedelta( hours=5 ) )
            data.append( row[1] )

        p.plot( times, data, label=indexes[i]['label'] )

    out_path = os.path.join( config.get( 'global', 'public_html' ),
        'covid-new_positives-{}.png'.format( t ) )
    p.save( out_path )



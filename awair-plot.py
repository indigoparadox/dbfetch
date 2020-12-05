#!/usr/local/bin/python2.7

from dbfetch import Plotter
from datetime import timedelta, datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ConfigParser import RawConfigParser
from models import Awair, create_awair
from matplotlib.dates import HourLocator, DateFormatter, DayLocator, MonthLocator
import os

config = RawConfigParser()
with open( '/home/dbfetch/awair.ini' ) as a:
    res = config.readfp( a )

db = create_engine( config.get( 'global', 'connection' ) )
create_awair( db )

Session = sessionmaker()    
Session.configure( bind=db )
session = Session()

intervals = {
    'day': {
        'start': datetime.now() - timedelta( days=1 ),
        'locator': HourLocator( interval=4 ),
        'formatter': DateFormatter( '%H:%M' ),
    },
    'week': {
        'start': datetime.now() - timedelta( days=7 ),
        'locator': DayLocator( interval=2 ),
        'formatter': DateFormatter( '%d' ),
    },
    'month': {
        'start': datetime.now() - timedelta( weeks=4 ),
        'locator': DayLocator( interval=2 ),
        'formatter': DateFormatter( '%d' ),
    },
    'year': {
        'start': datetime.now() - timedelta( days=365 ),
        'locator': MonthLocator( bymonthday=1, interval=1 ),
        'formatter': DateFormatter( '%m/%d' ),
    },
}
indexes = {
    'co2': {
        'field': Awair.co2,
        'title': 'CO2',
    },
}

for l in config.get( 'global', 'locations' ).split( ',' ):
    for t in intervals:
        for i in indexes:
            times = []
            data = []
            for row in session.query( Awair.timestamp, indexes[i]['field'] ) \
            .filter( Awair.timestamp >= intervals[t]['start'] ):
                # Timezone intervention.
                times.append( row[0] - timedelta( hours=5 ) )
                data.append( row[1] )

            title = '{} {}'.format(
                config.get( 'location-{}'.format( l ), 'title' ),
                indexes[i]['title'] )

            p = Plotter(
                title, intervals[t]['locator'], intervals[t]['formatter'] )

            p.plot( times, data )

            out_path = os.path.join( config.get( 'global', 'public_html' ),
                '{}-{}-{}.png'.format(
                    config.get( 'location-{}'.format( l ), 'output' ), i, t ) )
            p.save( out_path )


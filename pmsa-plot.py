#!/usr/local/bin/python2.7

from dbfetch import Plotter
from datetime import timedelta, datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ConfigParser import RawConfigParser
from models import PMSA, create_pmsa
import os

config = RawConfigParser()
with open( '/home/dbfetch/pmsa.ini' ) as a:
    res = config.readfp( a )

db = create_engine( config.get( 'global', 'connection' ) )
create_pmsa( db )

Session = sessionmaker()    
Session.configure( bind=db )
session = Session()

now = datetime.now()

indexes = {
    #'co2': {
    #    'field': PMSA.co2,
    #    'title': 'CO2',
    #},
    'voc': {
        'field': PMSA.tvoc,
        'title': 'TVOC',
    },
    'pm25': {
        'field': PMSA.particles_25um,
        'title': 'Particles < 2.5um',
    },
}

intervals = Plotter.intervals( now )
for l in config.get( 'global', 'locations' ).split( ',' ):
    for t in intervals:
        for i in indexes:
            times = []
            data = []
            for row in session.query( PMSA.timestamp, indexes[i]['field'] ) \
            .filter( PMSA.timestamp >= intervals[t]['start'] ):
                # Timezone intervention.
                times.append( row[0] - timedelta( hours=5 ) )
                data.append( row[1] )

            title = '{} {}'.format(
                config.get( 'location-{}'.format( l ), 'title' ),
                indexes[i]['title'] )

            p = Plotter(
                title, intervals[t]['locator'], intervals[t]['formatter'],
                w=intervals[t]['width'] )

            p.plot( times, data )

            out_path = os.path.join( config.get( 'global', 'public_html' ),
                '{}-{}-{}.png'.format(
                    config.get( 'location-{}'.format( l ), 'output' ), i, t ) )
            p.save( out_path )


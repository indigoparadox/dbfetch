#!/usr/local/bin/python2.7

import argparse
import logging
import sys
import os
import inspect
from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import sessionmaker
from dbfetch.request import Requester
from dbfetch.plot import Plotter
from ConfigParser import RawConfigParser, NoSectionError, NoOptionError
from datetime import datetime, timedelta

def import_module( module_key, module_path ):
    logger = logging.getLogger( 'import' )

    # Try (pretty hard) to import the module.
    module = None
    try:
        module = __import__( module_key, fromlist=[''] )
    except ImportError:
        # TODO: Configurable module import paths.
        logger.debug(
            'module {} not found, trying {}.{}...'.format(
                module_key, module_path, module_key ) )
        try:
            module = __import__( 
                '{}.{}'.format( module_path, module_key ), fromlist=[''] )
        except ImportError as e:
            logger.error( e )
            return None
    return module

def fetch( args, config ):
    logger = logging.getLogger( 'fetch' )

    # Run each requested module.
    for module_key in args.modules.split( ',' ):

        module = import_module( module_key, 'dbfetch.request' )

        eng = create_engine( config.get( module_key, 'connection' ) )
        with eng.connect() as db:

            logger.debug( 'ensuring schema...' )
            module.ModelRequester.model.create_all( db )

            locations = config.get( module_key, 'locations' ).split( ',' )
            for l in locations:
                logger.debug( 'checking location: {}...'.format( l ) )
                r = Requester( db, module.ModelRequester.transformations )
                json = Requester.request(
                    config.get( '{}-location-{}'.format(
                        module_key, l ), 'url' ) )
                for obj in r.format_json( json ):
                    obj['location'] = l
                    model = module.ModelRequester.model
                    timestamp_key = module.ModelRequester.timestamp_key
                    criteria = {timestamp_key: obj[timestamp_key]}
                    r.store(
                        obj, model, getattr( model, timestamp_key ),
                        **criteria )

                r.commit()

def plot_combined( module_key, module, args, config, session ):
    logger = logging.getLogger( 'plot.combined' )

    now = datetime.now()
    intervals = Plotter.intervals( now )
    indexes = module.ModelPlotter.indexes

    for l in config.get( module_key, 'locations' ).split( ',' ):
        for t in intervals:

            title = '{} {}'.format(
                config.get( '{}-location-{}'.format( module_key, l ), 'title' ),
                module.ModelPlotter.title )

            p = Plotter(
                title, intervals[t]['locator'], intervals[t]['formatter'],
                w=intervals[t]['width'] )

            for i in indexes:
                times = []
                data = []
                for row in session.query(
                module.ModelPlotter.timestamp, indexes[i]['field'] ) \
                .filter(
                module.ModelPlotter.timestamp >= intervals[t]['start'] ):
                    # Timezone intervention.
                    times.append( row[0] - timedelta( hours=5 ) )
                    data.append( row[1] )

                p.plot( times, data, label=indexes[i]['label'] )

            out_path = os.path.join(
                config.get( module_key, 'public_html' ),
                    '{}-{}-{}.png'.format(
                        config.get( '{}-location-{}'.format(
                            module_key, l ), 'output' ), i, t ) )
            p.save( out_path )

def plot_single( module_key, module, args, config, session ):
    logger = logging.getLogger( 'plot.single' )

    now = datetime.now()
    intervals = Plotter.intervals( now )
    indexes = module.ModelPlotter.indexes

    for l in config.get( module_key, 'locations' ).split( ',' ):
        for t in intervals:
            for i in indexes:
                times = []
                data = []
                for row in session.query(
                module.ModelPlotter.timestamp, indexes[i]['field'] ) \
                .filter(
                module.ModelPlotter.timestamp >= intervals[t]['start'] ):
                    # Timezone intervention.
                    times.append( row[0] - timedelta( hours=5 ) )
                    data.append( row[1] )

                title = '{} {}'.format(
                    config.get( '{}-location-{}'.format( module_key, l ),
                        'title' ),
                    indexes[i]['title'] )

                p = Plotter(
                    title, intervals[t]['locator'], intervals[t]['formatter'],
                    w=intervals[t]['width'] )

                p.plot( times, data )

                out_path = os.path.join(
                    config.get( module_key, 'public_html' ),
                        '{}-{}-{}.png'.format(
                            config.get( '{}-location-{}'.format(
                                module_key, l ), 'output' ), i, t ) )
                p.save( out_path )

def plot( args, config ):
    logger = logging.getLogger( 'plot' )

    # Plotter code is a bit more genericized because plotter data will always
    # come from the DB, while fetching the data originally could hypothetically
    # come from anywhere.

    # Run each requested module.
    for module_key in args.modules.split( ',' ):

        module = import_module( module_key, 'dbfetch.plot' )
        if not module:
            continue

        eng = create_engine( config.get( module_key, 'connection' ) )
        with eng.connect() as db:

            Session = sessionmaker()    
            Session.configure( bind=db )
            session = Session()

            # Try to setup and run the module.
            if 'combined' == module.ModelPlotter.index_plot:
                plot_combined( module_key, module, args, config, session )
            else:
                # Single plots by default.
                plot_single( module_key, module, args, config, session )

def main():

    # Deal with args.
    parser = argparse.ArgumentParser()

    sp = parser.add_subparsers()

    sp_fetch = sp.add_parser( 'fetch', help='fetches data and stores it' )
    sp_fetch.set_defaults( func=fetch )
    sp_fetch.add_argument( 'modules', action='store', nargs='?',
        help='select which modules to run, separated by commas' )

    sp_plot = sp.add_parser( 'plot', help='creates data graphic' )
    sp_plot.set_defaults( func=plot )
    sp_plot.add_argument( 'modules', action='store', nargs='?',
        help='select which modules to run, separated by commas' )

    parser.add_argument( '-v', '--verbose', action='store_true' )

    parser.add_argument(
        '-c', '--config', action='store', default='dbfetch.ini',
        help='specify config file; default is ' + \
            'dbfetch.ini in current directory' )

    if 2 >= len( sys.argv ):
        parser.print_help( sys.stderr )
        sys.exit( 1 )

    args = parser.parse_args()

    # Setup the logger.
    level = logging.ERROR
    if args.verbose:
        level = logging.DEBUG
    logging.basicConfig( level=level )
    logger = logging.getLogger( 'main' )

    # Setup config.
    config = RawConfigParser()
    with open( args.config ) as a:
        res = config.readfp( a )

    try:
        args.func( args, config )
    except (NoSectionError, NoOptionError) as e:
        logger.error( 'invalid module config: {}'.format( e ) )
    except ArgumentError as e:
        logger.error( 'database error: {}'.format( e ) )
            
if '__main__' == __name__:
    main()


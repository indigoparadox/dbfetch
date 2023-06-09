#!/usr/local/bin/python2.7

import argparse
import logging
import sys
import os
from ConfigParser import RawConfigParser, NoSectionError, NoOptionError
from datetime import datetime, timedelta

import sqlalchemy as sql
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import sessionmaker

from dbfetch.model import import_model
from dbfetch.plot import Plotter
from dbfetch.request import Requester

def fetch_mod( module_key, module, args, config, dbc ):

    logger = logging.getLogger( 'fetch.{}'.format( module_key ) )

    locations = config.get( module_key, 'locations' ).split( ',' )
    for loc in locations:
        logger.debug( 'checking location: %s...', loc )
       
        loc_config_key = '{}-location-{}'.format( module_key, loc )

        try:
            module['options']['ssl_verify'] = \
                config.get( loc_config_key, 'ssl_verify' )
        except NoOptionError:
            module['options']['ssl_verify'] = True

        req = Requester( dbc,
            module['transformations'], module['fields'], module['options'] )
        json = Requester.request(
            config.get( loc_config_key, 'url' ), module['options'] )
        for obj in req.format_json( json ):
            obj['location'] = loc
            criteria = {module['timestamp']: obj[module['timestamp']]}
            req.store(
                obj, module['model'],
                getattr( module['model'], module['timestamp'] ),
                **criteria )

        req.commit()

def fetch( args, config ):

    # Run each requested module.
    for module_key in args.modules.split( ',' ):

        eng = sql.create_engine( config.get( module_key, 'connection' ) )
        with eng.connect() as dbc:

            module = import_model( module_key, dbc, args.models )

            fetch_mod( module_key, module, args, config, dbc )

def plot_mod( module_key, module, args, config, session, combined=False ):
    logger = logging.getLogger( 'plot.combined' )

    now = datetime.now()
    intervals = Plotter.intervals( now )
    indexes = module['indexes']
    timestamp = getattr( module['model'], module['timestamp'] )

    l_cfg_key = None
    for loc in config.get( module_key, 'locations' ).split( ',' ):
        l_cfg_key = '{}-location-{}'.format( module_key, loc )
        tz_offset = 0
        plot = None # Initalize for scope.
        title = None # Initalize for scope.
        last_idx = None # Initalize for scope.

        try:
            tz_offset = config.getint( l_cfg_key, 'tz_offset' )
            logger.debug( 'using timezone offset of %d', tz_offset )
        except NoOptionError:
            logger.debug( 'no timezone offset specified; using 0' )

        def save_plot( plot_sav, idx, interval ):
            out_path = os.path.join(
                config.get( module_key, 'public_html' ),
                '{}-{}-{}.png'.format(
                    config.get( l_cfg_key, 'output' ), idx, interval ) )
            plot_sav.save( out_path )

        for inter in intervals:

            if combined:
                # Prepare the title for the whole plot.
                title = '{} {}'.format( config.get( l_cfg_key, 'title' ),
                    module['title'] )

                plot = Plotter(
                    title, intervals[inter]['locator'], intervals[inter]['formatter'],
                    w=intervals[inter]['width'] )

            for idx in indexes:
                times = []
                data = []
                for row in session.query( timestamp, indexes[idx]['field'] ) \
                .filter( timestamp >= intervals[inter]['start'] ):
                    # Timezone intervention.
                    times.append( row[0] + timedelta( hours=tz_offset ) )
                    data.append( row[1] )

                if combined:
                    # Just plot, save the combined plot later.
                    plot.plot( times, data, label=indexes[idx]['label'] )

                else:
                    # Plot and save.
                    title = '{} {}'.format( config.get( l_cfg_key, 'title' ),
                        indexes[idx]['title'] )

                    plot = Plotter(
                        title, intervals[inter]['locator'],
                        intervals[inter]['formatter'],
                        w=intervals[inter]['width'] )

                    plot.plot( times, data )

                    save_plot( plot, idx, inter )

                last_idx = idx

            if combined:
                save_plot( plot, last_idx, inter )

def plot_chart( args, config ):

    # Run each requested module.
    for module_key in args.modules.split( ',' ):

        eng = sql.create_engine( config.get( module_key, 'connection' ) )
        with eng.connect() as dbc:

            module = import_model( module_key, dbc, args.models )

            session_proto = sessionmaker()
            session_proto.configure( bind=dbc )
            session = session_proto()

            # Try to setup and run the module.
            plot_mod( module_key, module, args, config, session,
                combined=('combined' == module['index_plot']) )

def main():

    # Deal with args.
    parser = argparse.ArgumentParser()

    sub_p = parser.add_subparsers()

    sp_fetch = sub_p.add_parser( 'fetch', help='fetches data and stores it' )
    sp_fetch.set_defaults( func=fetch )
    sp_fetch.add_argument( 'modules', action='store', nargs='?',
        help='select which modules to run, separated by commas' )

    sp_plot = sub_p.add_parser( 'plot', help='creates data graphic' )
    sp_plot.set_defaults( func=plot_chart )
    sp_plot.add_argument( 'modules', action='store', nargs='?',
        help='select which modules to run, separated by commas' )

    parser.add_argument( '-v', '--verbose', action='store_true' )

    parser.add_argument(
        '-c', '--config', action='store', default='dbfetch.ini',
        help='specify config file; default is ' + \
            'dbfetch.ini in current directory' )

    parser.add_argument(
        '-m', '--models', action='store', default='models',
        help='specify path to model definition yml files' )

    if 2 >= len( sys.argv ):
        parser.print_help( sys.stderr )
        sys.exit( 1 )

    args = parser.parse_args()

    # Setup the logger.
    level = logging.WARNING
    if args.verbose:
        level = logging.DEBUG
    logging.basicConfig( level=level )
    logger = logging.getLogger( 'main' )

    # Setup config.
    config = RawConfigParser()
    with open( args.config ) as cfg_fp:
        config.readfp( cfg_fp )

    try:
        args.func( args, config )
    except (NoSectionError, NoOptionError) as e:
        logger.error( 'invalid module config: %s', e )
    except ArgumentError as e:
        logger.error( 'database error: %s', e )

if '__main__' == __name__:
    main()

#!/usr/local/bin/python2.7

import argparse
import sys
import socket
import os
from configparser import \
    RawConfigParser, \
    NoSectionError, \
    NoOptionError
from smtplib import SMTPServerDisconnected

import logging
from logging.handlers import SMTPHandler
from datetime import datetime

from sqlalchemy.exc import ArgumentError

from dbfetch.examples import copy_examples_to
from dbfetch.model import DBModelBuilder
from dbfetch.plot import Plotter
from dbfetch.fetch import Fetcher
from dbfetch.storage import Storage, StorageDuplicateException

CONFIG_DIRS = [
    '/etc/dbfetch',
    os.path.join( os.path.expanduser( '~' ), '.dbfetch' )
    #os.path.join( os.curdir, '.dbfetch' )
]

def fetch( storage, Model, **kwargs ):
    fetcher = Fetcher()
    for obj in fetcher.fetch_location( kwargs['url'], kwargs['location'] ):
        fmt_obj = Model.format_fetched_object( obj )
        try:
            storage.store( fmt_obj, Model, Model.timestamp_key )
        except StorageDuplicateException as exc:
            storage.log_duplicate( exc )

def plot( storage, Model, **kwargs ):
    plotter = Plotter( multi=Model.multi, **kwargs )
    interval_data = Plotter.intervals( datetime.now() )
    timestamp_comparator = getattr( Model, Model.timestamp_key )
    for interval in interval_data:
        query = storage.session.query( Model ) \
            .filter( timestamp_comparator >= interval_data[interval]['start'] )
        rows = query.all()

        for plot_iter in plotter.plot_location(
            interval,
            Model.timestamp_key,
            [r.__dict__ for r in rows],
            Model.plot_indexes,
            multi=Model.multi,
            **kwargs
        ):

            plot_iter.plot()
            plot_iter.save()
            plot_iter.close()

def main():

    # Deal with args.
    parser = argparse.ArgumentParser()

    sub_p = parser.add_subparsers()

    sp_fetch = sub_p.add_parser( 'fetch', help='fetches data and stores it' )
    sp_fetch.set_defaults( method=fetch )
    sp_fetch.add_argument( 'fetch_models', action='store', nargs='?',
        help='select which models to run, separated by commas' )

    sp_plot = sub_p.add_parser( 'plot', help='creates data graphic' )
    sp_plot.set_defaults( method=plot )
    sp_plot.add_argument( 'fetch_models', action='store', nargs='?',
        help='select which models to run, separated by commas' )

    parser.add_argument( '-v', '--verbose', action='store_true' )

    parser.add_argument(
        '-c', '--config', action='store',
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
    config_path = args.config
    if not config_path:
        for path_iter in CONFIG_DIRS:
            path_test = os.path.join( path_iter, 'dbfetch.ini' )
            logger.debug( 'searching for config in %s...', path_iter )
            if os.path.exists( path_test ):
                config_path = path_test
                break
    if not config_path:
        for path_iter in CONFIG_DIRS:
            logger.debug( 'try to create config in %s...', path_iter )
            try:
                copy_examples_to( path_iter )
            except IOError as exc:
                logger.debug( 'failed: %s', exc )
                continue
            logger.info( 'created new config in %s', path_iter )
            logger.info( 'modify %s to continue',
                os.path.join( path_iter, 'dbfetch.ini' ) )
            logger.info( 'see documentation for more information' )
            sys.exit( 1 )

    with open( config_path ) as cfg_fp:
        config.readfp( cfg_fp )

    try:
        mail_handler = SMTPHandler(
            mailhost=config.get( 'smtp', 'server' ),
            fromaddr=config.get( 'smtp', 'from' ),
            toaddrs=config.get( 'smtp', 'to'),
            subject='[dbfetch] Critical Error' )
        mail_handler.setLevel( logging.ERROR )
        logging.getLogger( None ).addHandler( mail_handler )
        #logger.error( 'testing critical error notification...' )
    except (SMTPServerDisconnected,
    NoSectionError,
    NoOptionError) as exc:
        #logging.getLogger( None ).removeHandler( mail_handler )
        logger.debug( 'unable to connect to mail server: %s', exc )

    if not args.fetch_models:
        logger.error( 'no models specified' )
        sys.exit( 1 )

    for model_key in args.fetch_models.split( ',' ):
        try:
            model_cfg = dict( config.items( model_key ) )
        except (NoOptionError, NoSectionError):
            logger.error( 'missing model configuration for %s', model_key )
            continue
        Model = None

        try:
            with Storage( model_cfg['connection'] ) as storage:
                if args.models:
                    model_path = os.path.join( args.models,
                        '{}.yml'.format( model_key ) )
                    if os.path.exists( model_path ):
                        Model = DBModelBuilder.import_model(
                            model_path, storage.db )
                else:
                    # Check each config dir for a models dir.
                    for path_iter in CONFIG_DIRS:
                        model_path = os.path.join( path_iter, 'models',
                            '{}.yml'.format( model_key ) )
                        if os.path.exists( model_path ):
                            Model = DBModelBuilder.import_model(
                                model_path, storage.db )
                            break
                if not Model:
                    logger.error( 'unable to find %s.yml', model_key )
                    continue

                for location in model_cfg['locations']:
                    location_args = model_cfg.copy()
                    location_args.update(
                        dict( config.items(
                            '{}-location-{}'.format( model_key, location ) ) ) )
                    location_args['location'] = location

                    # Check for new columns.
                    # TODO: Maybe dynamically detect new columns from fetch?
                    for col_name in Model.columns:
                        storage.add_column_if_not_exist(
                            Model.__tablename__, Model.columns[col_name] )

                    args.method( storage, Model, **location_args )
        except ArgumentError as exc:
            logger.error( 'database error: %s', exc )
            continue

if '__main__' == __name__:
    main()

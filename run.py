#!/usr/local/bin/python2.7

import argparse
import sys
from ConfigParser import RawConfigParser, NoSectionError, NoOptionError

import logging
from logging.handlers import SMTPHandler

from sqlalchemy.exc import ArgumentError

from dbfetch.plot import Plotter
from dbfetch.fetch import fetch

def main():

    # Deal with args.
    parser = argparse.ArgumentParser()

    sub_p = parser.add_subparsers()

    sp_fetch = sub_p.add_parser( 'fetch', help='fetches data and stores it' )
    sp_fetch.set_defaults( func=fetch )
    sp_fetch.add_argument( 'modules', action='store', nargs='?',
        help='select which modules to run, separated by commas' )

    sp_plot = sub_p.add_parser( 'plot', help='creates data graphic' )
    sp_plot.set_defaults( func=Plotter.plot_chart )
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
        mail_handler = SMTPHandler(
            mailhost=config.get( 'smtp', 'server' ),
            fromaddr=config.get( 'smtp', 'from' ),
            toaddrs=config.get( 'smtp', 'to'),
            subject='[dbfetch] Critical Error' )
        mail_handler.setLevel( logging.ERROR )
        logging.getLogger( None ).addHandler( mail_handler )
    except Exception as e:
        logger.debug( 'error setting up mail handler: %s', e )

    if args.verbose:
        logger.error( 'testing critical error notification...' )

    try:
        args.func( args, config )
    except (NoSectionError, NoOptionError) as e:
        logger.error( 'invalid module config: %s', e )
    except ArgumentError as e:
        logger.error( 'database error: %s', e )

if '__main__' == __name__:
    main()

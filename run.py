#!/usr/local/bin/python2.7

import argparse
import logging
import sys
import inspect
from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError
from dbfetch.request import Requester
from ConfigParser import RawConfigParser, NoSectionError, NoOptionError
from datetime import datetime

def fetch( args, config ):
    logger = logging.getLogger( 'fetch' )

    # Run each requested module.
    for module_key in args.modules.split( ',' ):

        # Try (pretty hard) to import the module.
        module = None
        try:
            module = __import__( module_key, fromlist=[''] )
        except ImportError:
            logger.debug(
                'module {} not found, trying dbfetch.request.{}...'.format(
                    module_key, module_key ) )
            try:
                module = __import__( 
                    'dbfetch.request.{}'.format( module_key ), fromlist=[''] )
            except ImportError as e:
                logger.error( e )
                continue

        eng = create_engine( config.get( module_key, 'connection' ) )
        with eng.connect() as db:
            # Try to setup and run the module.
            r = module.ModelRequester( db, config )
            r.fetch()

def main():

    # Deal with args.
    parser = argparse.ArgumentParser()

    sp = parser.add_subparsers()
    sp_fetch = sp.add_parser( 'fetch', help='fetches data and stores it' )
    sp_plot = sp.add_parser( 'plot', help='creates data graphic' )

    sp_fetch.add_argument( 'modules', action='store', nargs='?',
        help='select which modules to run, separated by commas' )

    sp_fetch.set_defaults( func=fetch )

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


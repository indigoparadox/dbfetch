#!/usr/local/bin/python2.7

import argparse
import logging
import sys
import inspect
from sqlalchemy import create_engine
from dbfetch.request import Requester
from ConfigParser import RawConfigParser
from datetime import datetime

def fetch( module_key, db, config ):
    logger = logging.getLogger( 'fetch' )

    # Try to setup and run the module.
    module = None
    try:
        module = __import__( module_key, fromlist=[''] )
    except ImportError:
        logger.debug(
            'module {} not found, trying dbfetch.request.{}...'.format(
                module_key, module_key ) )
        module_key = 'dbfetch.request.{}'.format( module_key )
        module = __import__( module_key, fromlist=[''] )

    r = module.ModelRequester( db, config )
    r.fetch()

def main():

    # Deal with args.
    # TODO: More helpful error handling.
    parser = argparse.ArgumentParser()

    parser.add_argument( '-v', '--verbose', action='store_true' )

    parser.add_argument(
        '-c', '--config', action='store', default='dbfetch.ini' )

    parser.add_argument( '-m', '--modules', action='store' )

    args = parser.parse_args()

    # Setup the logger.
    level = logging.ERROR
    if args.verbose:
        level = logging.DEBUG
    logging.basicConfig( level=level )
    logger = logging.getLogger( 'main' )

    # Grab a list of modules to run.
    modules_run = args.modules.split( ',' )

    # Setup config.
    config = RawConfigParser()
    with open( args.config ) as a:
        res = config.readfp( a )

    # Run each requested module.
    for module_key in modules_run:
        eng = create_engine( config.get( module_key, 'connection' ) )
        with eng.connect() as db:
            fetch( module_key, db, config )
            
if '__main__' == __name__:
    main()


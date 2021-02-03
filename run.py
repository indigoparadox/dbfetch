#!/usr/local/bin/python2.7

import argparse
import logging
import sys
import inspect
import dbfetch.models
from sqlalchemy import create_engine
from dbfetch.request import Requester
from ConfigParser import RawConfigParser
from datetime import datetime

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

    # Setup active DBs.
    dbs = {}
    for module in modules_run:
        dbs[module] = create_engine( config.get( module, 'connection' ) )

    # Grab a list of currently available models to work with.
    # TODO: Make this more modular? Work with models outside the package?
    model_objects = {}
    m = sys.modules['dbfetch.models']
    for name, cls in inspect.getmembers( m ):
        #if str( cls ).startswith( 'dbfetch.models' ):
        if not name.startswith( 'Base' ) and \
        not name.startswith( '_' ) and \
        not name.startswith( 'create' ) and \
        not name == 'declarative_base' and \
        not name == 'sql':
            logger.debug( 'found model: {}'.format( name ) )
            model_objects[name] = cls

    # Setup DB metadata.
    for key in model_objects:
        if key.lower() in dbs:
            logger.debug( 'creating db schema for {}...'.format( key ) )
            model_objects[key].create_all( dbs[key.lower()] )

if '__main__' == __name__:
    main()


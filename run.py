#!/usr/local/bin/python2.7

import argparse
import logging
import sys
import os
import inspect
import sqlalchemy as sql
import yaml
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dbfetch.request import Requester
from dbfetch.plot import Plotter
from ConfigParser import RawConfigParser, NoSectionError, NoOptionError
from datetime import datetime, timedelta

def import_model( module_key, db, models_path ):

    logger = logging.getLogger( 'model.import' )

    BaseModel = declarative_base()

    model_def = None
    model_path = os.path.join( models_path, '{}.yml'.format( module_key ) )
    with open( model_path, 'r' ) as m_file:
        model_def = yaml.load( m_file )

    model_fields = {}
    for field_key in model_def['fields']:
        field_def = model_def['fields'][field_key]

        # The sz is special since it gets passed to the type.
        type_args = []
        if 'sz' in field_def:
            type_args.append( int( field_def['sz'] ) )
            field_def.pop( 'sz' )

        # Create the column.
        if 'float' == field_def['type']:
            field_def.pop( 'type' )
            model_fields[field_key] = \
                sql.Column( sql.Float( *type_args ), **field_def )
        elif 'int' == field_def['type']:
            field_def.pop( 'type' )
            model_fields[field_key] = \
                sql.Column( sql.Integer( *type_args ), **field_def )
        elif 'datetime' == field_def['type']:
            field_def.pop( 'type' )
            model_fields[field_key] = \
                sql.Column( sql.DateTime( *type_args ), **field_def )
        elif 'string' == field_def['type']:
            field_def.pop( 'type' )
            model_fields[field_key] = \
                sql.Column( sql.String( *type_args ), **field_def )

    model_fields['__tablename__'] = model_def['tablename']
    
    model = type( 'FetchModel', (BaseModel,), model_fields )

    logger.debug( 'ensuring fields for {}...'.format( module_key ) )
    BaseModel.metadata.create_all( db )

    # Parse transformations.
    t_func_out = lambda o: o
    for t_key in model_def['transformations']:
        for t_iter in model_def['transformations'][t_key]:
            t_path = t_iter.split( '.' )

            # Descend from root element in globals() to a method/class (if any).
            if 'int' == t_path[0]:
                t_func_out = lambda o: int( o )
            else:
                t_func = globals()[t_path[0]]
                t_path.pop( 0 )
                while 0 < len( t_path ):
                    t_func = getattr( t_func, t_path[0] )
                    t_path.pop( 0 )

                t_func_out = lambda o: t_func( o )
        model_def['transformations'][t_key] = t_func_out

    # Tidy up parsed fields and attach resulting model.
    model_def.pop( 'fields' )
    model_def.pop( 'tablename' )
    model_def['model'] = model

    return model_def

def fetch( args, config ):
    logger = logging.getLogger( 'fetch' )

    # Run each requested module.
    for module_key in args.modules.split( ',' ):

        eng = sql.create_engine( config.get( module_key, 'connection' ) )
        with eng.connect() as db:

            module = import_model( module_key, db, args.models )

            locations = config.get( module_key, 'locations' ).split( ',' )
            for l in locations:
                logger.debug( 'checking location: {}...'.format( l ) )
                r = Requester( db, module['transformations'] )
                json = Requester.request(
                    config.get( '{}-location-{}'.format(
                        module_key, l ), 'url' ) )
                for obj in r.format_json( json ):
                    obj['location'] = l
                    model = module['model']
                    criteria = {module['timestamp']: obj[module['timestamp']]}
                    r.store(
                        obj, model, getattr( model, module['timestamp'] ),
                        **criteria )

                r.commit()

def plot_combined( module_key, module, args, config, session ):
    logger = logging.getLogger( 'plot.combined' )

    now = datetime.now()
    intervals = Plotter.intervals( now )
    indexes = module['indexes']
    timestamp = getattr( module['model'], module['timestamp'] )

    for l in config.get( module_key, 'locations' ).split( ',' ):
        for t in intervals:

            title = '{} {}'.format(
                config.get( '{}-location-{}'.format( module_key, l ), 'title' ),
                module['title'] )

            p = Plotter(
                title, intervals[t]['locator'], intervals[t]['formatter'],
                w=intervals[t]['width'] )

            for i in indexes:
                times = []
                data = []
                for row in session.query( timestamp, indexes[i]['field'] ) \
                .filter( timestamp >= intervals[t]['start'] ):
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
    indexes = module['indexes']
    timestamp = getattr( module['model'], module['timestamp'] )

    for l in config.get( module_key, 'locations' ).split( ',' ):
        for t in intervals:
            for i in indexes:
                times = []
                data = []
                for row in session.query( timestamp, indexes[i]['field'] ) \
                .filter( timestamp >= intervals[t]['start'] ):
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

        eng = sql.create_engine( config.get( module_key, 'connection' ) )
        with eng.connect() as db:

            module = import_model( module_key, db, args.models )

            Session = sessionmaker()    
            Session.configure( bind=db )
            session = Session()

            # Try to setup and run the module.
            if 'combined' == module['index_plot']:
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

    parser.add_argument(
        '-m', '--models', action='store', default='models',
        help='specify path to model definition yml files' )

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


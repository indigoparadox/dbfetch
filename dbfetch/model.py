
import logging
import os
import yaml
import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from dbfetch.request import Requester
from dbfetch.plot import Plotter

def create_model( db, model_def ):

    ''' Create the given table in the database with its primary key if it does
    not exist. '''

    logger = logging.getLogger( 'model.create' )

    inspector = Inspector.from_engine( db )

    # Build the CREATE TABLE parameters for just the primary keys.
    # Other fields can be added in import_model() later.
    table_field_defs = []
    table_keys = []
    for field_key in model_def['fields']:
        field_def = model_def['fields'][field_key]
        if 'primary_key' in field_def and field_def['primary_key']:

            # We don't handle modifiers here so only allow simple types for now.
            assert( 'datetime' == field_def['type'] or \
                'int' == field_def['type'] )

            table_field_defs.append( '{} {} NOT NULL'.format(
                field_key, field_def['type'] ) )
            table_keys.append( field_key )

    table_field_defs.append(
        'PRIMARY KEY ({})'.format( ','.join( table_keys ) ) )

    db.execute( 'CREATE TABLE {} ({})'.format(
        model_def['tablename'], ','.join( table_field_defs ) ) )

    logger.info( 'table %s created with primary keys: %s',
        model_def['tablename'], ','.join( table_keys ) )

def import_model( module_key, db, models_path ):

    logger = logging.getLogger( 'model.import' )

    BaseModel = declarative_base()
    inspector = Inspector.from_engine( db )

    model_def = None
    model_path = os.path.join( models_path, '{}.yml'.format( module_key ) )
    with open( model_path, 'r' ) as m_file:
        model_def = yaml.load( m_file )

    if not model_def['tablename'] in inspector.get_table_names():
        logger.info(
            'database table %s does not exist! attempting to create...',
            model_def['tablename'] )
        create_model( db, model_def )

    model_fields = {}
    for field_key in model_def['fields']:
        field_def = model_def['fields'][field_key]

        # The sz is special since it gets passed to the type.
        type_args = []
        if 'sz' in field_def:
            type_args.append( str( field_def['sz'] ) )
            field_def.pop( 'sz' )

        db_columns = [c['name'] for c in inspector.get_columns(
            model_def['tablename'] )]
        if not field_key in db_columns:
            logger.warning( 'field %s not found in table; creating...',
                field_key )

            # Create the column in the database table.
            db.execute( 'ALTER TABLE {} ADD COLUMN {} {}{}'.format(
                model_def['tablename'],
                field_key,
                model_def['fields'][field_key]['type'],
                '' if 0 == len( type_args ) else '({})'.format(
                    ','.join( type_args ) ) ) )

        # Create the column in our SQLAlchemy model.
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
    t_func_out = lambda o, k: o[k]
    for t_key in model_def['transformations']:
        for t_iter in model_def['transformations'][t_key]:

            t_path = t_iter.split( '.' )

            # Descend from root element in globals() to a method/class (if any).
            if 'int' == t_path[0]:
                t_func_out = lambda o, k: int( o[k] )
                logger.debug( 'adding %s transformation: int', t_key )
            else:
                t_func = globals()[t_path[0]]
                t_path.pop( 0 )
                while 0 < len( t_path ):
                    t_func = getattr( t_func, t_path[0] )
                    t_path.pop( 0 )

                t_func_out = lambda o, k: t_func( o, k )
                logger.debug( 'adding %s transformation: %s (y: %s)',
                    t_key, t_func, t_func_out )
        model_def['transformations'][t_key] = t_func_out

    # Tidy up parsed fields and attach resulting model.
    #model_def.pop( 'fields' )
    model_def.pop( 'tablename' )
    model_def['model'] = model

    return model_def


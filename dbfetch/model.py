
import logging
import os
import yaml
import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
from dbfetch.request import Requester
from dbfetch.plot import Plotter

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


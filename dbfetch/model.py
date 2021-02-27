
import logging
import os
import math # For transforms.
from datetime import datetime # For transforms.

import yaml
import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base

class DBModelTimestampException( Exception ):
    pass

class ModelFormatterMixin( object ):

    @classmethod
    def format_fetched_obj( cls, obj ):

        for key in obj:
            if key in cls.transforms:
                new_value = cls.transforms[key]( obj[key] )
                cls.logger.debug( 'replacing %s with %s', obj[key], new_value )
                obj[key] = new_value

        return obj

    @classmethod
    def format_fetched_data( cls, data ):
        if isinstance( data, list ):
            for obj in data:
                obj = cls.format_fetched_obj( obj )
                yield obj
        else:
            yield cls.format_fetched_obj( data )

class ModelTransforms( object ):
    @staticmethod
    def str_date_no_z( date_str ):
        return datetime.strptime(
            date_str.replace( 'Z', '' ), '%Y-%m-%dT%H:%M:%S.%f' )

class DBModelBuilder( object ):

    def __init__( self, table_name, index_plot='single' ):

        self.model_fields = {
            '__tablename__': table_name
        }
        self.plot_indexes = {}
        self.logger = logging.getLogger( 'model' )
        self.transforms = {}
        self.base = declarative_base()
        self.multi = True if 'multi' == index_plot else False

    @staticmethod
    def type_args( field_def, modify=True ):

        # The sz is special since it gets passed to the type.
        type_args = []
        if 'sz' in field_def:
            type_args.append( int( field_def['sz'] ) )
            del field_def['sz']

        return type_args

    def add_column( self, field_def ):

        field_def = field_def.copy()

        type_args = DBModelBuilder.type_args( field_def )

        is_timestamp = False
        field_type = field_def['type']
        del field_def['type']

        if 'index_as' in field_def:
            self.plot_indexes[field_def['name']] = field_def['index_as']
            del field_def['index_as']
        if 'transformations' in field_def:
            for t_iter in field_def['transformations']:
                self.add_transformation( field_def['name'], t_iter )
            del field_def['transformations']
        if 'timestamp' in field_def:
            if field_def['timestamp']:
                is_timestamp = True
            del field_def['timestamp']

        if 'float' == field_type:
            self.model_fields[field_def['name']] = \
                sql.Column( sql.Float( *type_args ), **field_def )
        elif 'int' == field_type:
            self.model_fields[field_def['name']] = \
                sql.Column( sql.Integer( *type_args ), **field_def )
        elif 'datetime' == field_type:
            self.model_fields[field_def['name']] = \
                sql.Column( sql.DateTime( *type_args ), **field_def )
            if is_timestamp:
                # Purposely not defined in init so tests work later.
                self.timestamp = self.model_fields[field_def['name']]
        elif 'string' == field_type:
            self.model_fields[field_def['name']] = \
                sql.Column( sql.String( *type_args ), **field_def )

    def add_transformation( self, field, transform ):

        t_path = transform.split( '.' )
        t_func = None

        # Descend from root element in globals() to a method/class (if any).
        if 'int' == t_path[0]:
            t_func = lambda o: int( o )
        elif 'float' == t_path[0]:
            t_func = lambda o: float( o )
        else:
            t_func = globals()[t_path[0]]
            t_path.pop( 0 )
            while t_path:
                t_func = getattr( t_func, t_path[0] )
                t_path.pop( 0 )

        if field in self.transforms:
            prev_func = self.transforms[field]
            self.transforms[field] = \
                lambda o: t_func( prev_func( o ) )
        else:
            self.transforms[field] = lambda o: t_func( o )

    def build_model( self ):

        # Prepare utility classmethods to attach to the model class we're
        # building.
        self.model_fields['format_fetched_object'] = classmethod(
            lambda cls, o: {
                ok: (cls.transforms[ok]( ov ) if ok in cls.transforms else ov)
                for ok, ov in o.items()} )

        # Dynamically create the new model class.
        FetchModel = type(
            'FetchModel',
            (self.base,),
            self.model_fields )

        # All data processed through this utility needs a timestamp.
        if not hasattr( self, 'timestamp' ):
            raise DBModelTimestampException( 'no timestamp column' )
        FetchModel.timestamp_key = self.timestamp.name
        FetchModel.transforms = self.transforms
        FetchModel.multi = self.multi
        FetchModel.plot_indexes = self.plot_indexes

        return FetchModel

    def create_table( self, db ):

        self.logger.debug( 'ensuring fields for %s...',
            self.model_fields['__tablename__'] )
        self.base.metadata.create_all( db )

    @staticmethod
    def import_model( module_key, db, models_path ):

        model_def = None
        model_path = os.path.join( models_path, '{}.yml'.format( module_key ) )
        with open( model_path, 'r' ) as m_file:
            model_def = yaml.load( m_file )

        builder = DBModelBuilder(
            model_def['tablename'], model_def['index_plot'] )

        for field_key in model_def['fields']:
            field_def = model_def['fields'][field_key]
            field_def['name'] = field_key

            # Create the column in our SQLAlchemy model.
            builder.add_column( field_def )

        Model = builder.build_model()
        builder.create_table( db )

        return Model


import logging
import sqlalchemy as sql
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.reflection import Inspector

from .model import DBModelBuilder

class StorageDuplicateException( Exception ):
    pass

class Storage( object ):

    def __init__( self, db_url ):
        self.db = None
        self.engine = None
        self.session = None
        self._db_url = None
        self.db_url = db_url
        self.logger = logging.getLogger( 'storage' )

    def __enter__( self ):
        self.setup()
        return self

    def __exit__( self, type, value, traceback ):
        self.close()

    @property
    def db_url( self ):
        return self._db_url

    @db_url.setter
    def db_url( self, value ):
        assert( None == self.db )
        assert( None == self.session )
        self.engine = sql.create_engine( value )
        self._db_url = value

    def setup( self ):
        self.logger.debug( 'connecting to database: %s', self._db_url )
        self.db = self.engine.connect()
        Session = sessionmaker()
        Session.configure( bind=self.db )
        self.session = Session()

    def close( self ):
        self.db.close()
        self.db = None
        self.session = None

    def log_duplicate( self, exc ):
        self.logger.warning( 'duplicate row not stored: %s', exc )

    def add_column_if_not_exist( self, table_name, field_def ):

        inspector = Inspector.from_engine( self.db )
        type_args = DBModelBuilder.type_args( field_def )

        db_columns = [c['name'] for c in inspector.get_columns( table_name )]
        if [] != db_columns and not field_def['name'] in db_columns:
            self.logger.warning( 'field %s not found in table; creating...',
                field_def['name'] )

            type_args_str = ''
            if type_args:
                type_args_str = ','.join( [str( a ) for a in type_args] )

            # Create the column in the database table.
            self.db.execute( 'ALTER TABLE {} ADD COLUMN {} {}{}'.format(
                table_name,
                field_def['name'],
                field_def['type'],
                type_args_str ) )

    def store( self, data, model, f_col_name ):

        if not self.session.query( model ) \
        .filter( getattr( model, f_col_name ).__eq__( data[f_col_name] )
        ).scalar():
            self.logger.debug( 'storing new data: %s', data )
            db_row = model( **data )
            self.session.add( db_row )
            self.session.commit()
        else:
            raise StorageDuplicateException( 'duplicate {}: {}'.format(
                f_col_name, data[f_col_name] ) )

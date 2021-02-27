
import unittest

from sqlalchemy.exc import OperationalError, IntegrityError
from faker import Faker

from fake_model import FakeModel
from dbfetch.storage import Storage, StorageDuplicateException
from dbfetch.model import DBModelBuilder

class TestStorage( unittest.TestCase ):

    def setUp( self ):

        self.storage = Storage( 'sqlite:///' )
        self.storage.setup()
        self.fake = Faker()
        self.fake.add_provider( FakeModel )
        self.builders = []

        return super( TestStorage, self ).setUp()

    def tearDown( self ):

        for builder in self.builders:
            builder.base.metadata.drop_all( bind=self.storage.db )
        self.storage.close()

        return super( TestStorage, self ).tearDown()

    def test_add_column_if_not_exist( self ):

        def create_model( field_defs ):
            builder = DBModelBuilder( 'test_table' )
            for field_def in field_defs:
                builder.add_column( field_def )
            Model = builder.build_model()
            builder.create_table( self.storage.db )
            self.builders.append( builder )
            return Model

        def dump_table():
            res = self.storage.db.execute( 'select * from test_table' )
            print( '---' )
            for r in res:
                print( r )
            print( '---' )

        orig_schema = self.fake.schema()
        OrigModel = create_model( orig_schema )
        orig_row = self.fake.row( orig_schema )

        new_schema = orig_schema[:]
        new_column = self.fake.field_def()
        while new_column['name'] in [c['name'] for c in orig_schema]:
            # Don't add if duplicate.
            new_column = self.fake.field_def()
        new_column['nullable'] = False
        new_schema.append( new_column )

        NewModel = create_model( new_schema )

        # Make sure the original row can be added.
        self.storage.session.add( OrigModel( **orig_row ) )
        self.storage.session.commit()
        
        self.new_builder = DBModelBuilder( 'test_table' )
        for field_def in orig_schema:
            self.new_builder.add_column( field_def )
        new_row = self.fake.row( new_schema )

        # Make sure the new row can't be added yet.
        self.storage.session.add( NewModel( **new_row ) )
        with self.assertRaises( OperationalError ):
            self.storage.session.commit()
        self.storage.session.rollback()

        self.storage.add_column_if_not_exist( 'test_table', new_column )

        # Make sure the original row can no longer be added.
        self.assertTrue( hasattr( NewModel, new_column['name'] ) )
        self.assertFalse( hasattr( OrigModel, new_column['name'] ) )
        self.assertNotIn( new_column['name'], orig_row )
        with self.assertRaises( IntegrityError ):
            self.storage.session.add( OrigModel( **orig_row ) )
            self.storage.session.commit()

    def test_store( self ):

        field_defs = self.fake.schema()
        builder = DBModelBuilder( 'test_table' )
        for field_def in field_defs:
            builder.add_column( field_def )
        Model = builder.build_model()
        builder.create_table( self.storage.db )
        self.builders.append( builder )

        row = self.fake.row( field_defs )
        self.storage.store( row, Model, 'timestamp' )

        with self.assertRaises( StorageDuplicateException ):
            self.storage.store( row, Model, 'timestamp' )

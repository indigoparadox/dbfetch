
import unittest
import sys
import os
from datetime import datetime
import sqlalchemy as sql
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.schema import Column
from faker import Faker
from sqlalchemy.orm.attributes import InstrumentedAttribute

sys.path.insert( 0, os.path.dirname( os.path.dirname( __file__) ) )

from dbfetch.model import DBModelBuilder, ModelTransforms
from fake_model import FakeModel

class TestModel( unittest.TestCase ):

    def setUp( self ):

        self.db = sql.create_engine( 'sqlite:///' )
        self.dbc = self.db.connect()
        self.builder = DBModelBuilder( 'test_table' )
        self.fake = Faker()
        self.fake.add_provider( FakeModel )

        Session = sessionmaker()
        Session.configure( bind=self.dbc )
        self.session = Session()

        return super( TestModel, self ).setUp()

    def tearDown( self ):

        self.builder.base.metadata.drop_all( bind=self.dbc )
        self.dbc.close()

        return super( TestModel, self ).tearDown()

    def test_model_create( self ):

        fields = self.fake.schema()

        for field_def in fields:
            self.builder.add_column( field_def )

        Model = self.builder.build_model()

        for field_def in fields:
            self.assertTrue( hasattr( Model, field_def['name'] ) )

    def test_model_add_column( self ):

        fields = self.fake.schema()

        for field_def in fields:
            self.builder.add_column( field_def )

        Model = self.builder.build_model()

        self.assertTrue( hasattr( Model, fields[0]['name'] ) )
        self.assertIsInstance( getattr( Model, fields[1]['name'] ),
            InstrumentedAttribute )

        self.assertTrue( hasattr( Model, fields[1]['name'] ) )
        self.assertIsInstance( getattr( Model, fields[1]['name'] ),
            InstrumentedAttribute )

    def test_add_transformation( self ):

        field_def = {
            'name': 'test_math',
            'type': 'float',
            'transformations': [
                'float',
                'math.sqrt'
            ]
        }
        self.builder.add_column( field_def )

        test_data = {
            'key': 1,
            'timestamp': datetime.now(),
            'test_math': '4' }

        self.assertEqual(
            2.0,
            self.builder.transforms['test_math']( test_data['test_math'] ) )

    def test_timestamp( self ):
        field_def = {
            'name': 'test_int',
            'type': 'int',
            'primary_key': True
        }
        self.builder.add_column( field_def )

        self.assertFalse( hasattr( self.builder, 'timestamp' ) )

        field_def = {
            'name': 'test_ts',
            'type': 'datetime',
            'timestamp': True
        }
        self.builder.add_column( field_def )

        Model = self.builder.build_model()
        self.builder.create_table( self.dbc )

        self.assertEqual( self.builder.timestamp, getattr( Model, Model.timestamp_key ) )
        self.assertEqual( type( self.builder.timestamp ), Column )

    @unittest.expectedFailure
    def test_format_data( self ):

        schema = self.fake.schema()
        row = self.fake.row( schema )

        row['timestamp'] = 12345

        for field in schema:
            self.builder.add_column( field )
        Model = self.builder.build_model()
        self.builder.create_table( self.dbc )

        store_row = Model.format_fetched_object( row )

        self.assertEqual(
            store_row['timestamp'],
            datetime( 1969, 12, 31, 22, 25, 45 )
        )

    def test_model_transforms( self ):
        
        timestamp = datetime.now()
        schema = self.fake.schema( timestamp_str=True )
        row = self.fake.row( schema, datetime_as='string', timestamp=timestamp )

        for field in schema:
            self.builder.add_column( field )
        Model = self.builder.build_model()
        self.builder.create_table( self.dbc )

        store_row = Model.format_fetched_object( row )

        self.assertEqual(
            store_row['timestamp'],
            timestamp
        )

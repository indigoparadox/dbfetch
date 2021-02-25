
import unittest
import sys
import os
import sqlalchemy as sql

sys.path.insert( 0, os.path.dirname( os.path.dirname( __file__) ) )

from dbfetch.model import import_model

class TestModel( unittest.TestCase ):

    def setUp( self ):

        self.db = sql.create_engine( 'sqlite:///' )

        return super( TestModel, self ).setUp()

    def tearDown( self ):
        return super( TestModel, self ).tearDown()

    def test_model_create( self ):
        pmsa_module = import_model( 'pmsa', self.db, './models' )
        pmsa_model = pmsa_module['model']

        self.assertIsInstance( pmsa_model, 'FetchModel' )

        print( pmsa_model )

    def test_model_new_column( self ):
        pass

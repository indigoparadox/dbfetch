
import tempfile
import unittest
import shutil
import os
import sys
from contextlib import contextmanager

sys.path.insert( 0, os.path.dirname( os.path.dirname( __file__) ) )

from dbfetch.examples import copy_examples_to

class TestExamples( unittest.TestCase ):

    @contextmanager
    def create_temp_dir( self ):
        tempdir_path = tempfile.mkdtemp()
        try:
            yield tempdir_path
        finally:
            shutil.rmtree( tempdir_path )

    def test_copy_examples( self ):

        with self.create_temp_dir() as tempdir_path:

            os.mkdir( os.path.join( tempdir_path, 'models' ) )

            copy_examples_to( tempdir_path )

            test_examples = [
                'models/awair.yml',
                'models/covid.yml',
                'models/pmsa.yml'
            ]

            for ex in test_examples:
                test_path = os.path.join( tempdir_path, ex )
                self.assertTrue( os.path.exists( test_path ) )

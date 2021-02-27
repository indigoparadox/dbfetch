
import unittest
import os
import sys
import json
import threading
import random
try:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
    from SocketServer import ThreadingMixIn
except ImportError:
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from socketserver import ThreadingMixIn

from faker import Faker

sys.path.insert( 0, os.path.dirname( os.path.dirname( __file__) ) )

from dbfetch.fetch import Fetcher
from fake_model import FakeModel

class FetchHandler( BaseHTTPRequestHandler ):

    ''' Simple dummy JSON server handler for testing. '''

    def do_GET( self ):
        self.send_response( 200 )
        self.end_headers()
        self.wfile.write( json.dumps( self.server.data ).encode( 'utf-8' ) )

class FetchServer( ThreadingMixIn, HTTPServer ):

    ''' Simple dummy JSON server for testing. '''

    daemon_threads = True

class TestFetch( unittest.TestCase ):

    def setUp( self ):
        self.fake = Faker()
        self.fake.add_provider( FakeModel )
        self.server = FetchServer( ('127.0.0.1', 58765), FetchHandler )
        self.server.data = []
        self.server_thread = threading.Thread( target=self.server.serve_forever )
        self.server_thread.daemon = True
        self.server_thread.start()
        return super( TestFetch, self ).setUp()

    def tearDown( self ):
        self.server.shutdown()
        self.server.server_close()
        return super( TestFetch, self ).tearDown()

    def test_fetch_location_list( self ):

        schema = self.fake.schema()
        timestamp_key = [c['name'] for c in schema if 'timestamp' in c][0]
        fake_data = []
        for i in range( 1000 ):
            row = self.fake.row( schema )
            row[timestamp_key] = random.randint( 11140000, 19950000 )
            fake_data.append( row )
        self.server.data = fake_data

        fetcher = Fetcher()

        idx = 0
        for fetched in fetcher.fetch_location( 'http://127.0.0.1:58765/fake.json', '1' ):
            fake_data[idx]['location'] = '1'
            self.assertDictEqual( fetched, fake_data[idx] )
            idx += 1

    def test_fetch_location( self ):

        schema = self.fake.schema()
        timestamp_key = [c['name'] for c in schema if 'timestamp' in c][0]
        fake_row = self.fake.row( schema )
        fake_row[timestamp_key] = random.randint( 11140000, 19950000 )
        self.server.data = fake_row

        fetcher = Fetcher()

        for fetched in fetcher.fetch_location( 'http://127.0.0.1:58765/fake.json', '1' ):
            fake_row['location'] = '1'
            self.assertDictEqual( fetched, fake_row )

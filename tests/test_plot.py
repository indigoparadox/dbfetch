
import unittest
import sys
import os
from datetime import datetime, timedelta

import sqlalchemy as sql
from sqlalchemy.orm import sessionmaker
from faker import Faker

sys.path.insert( 0, os.path.dirname( os.path.dirname( __file__) ) )

from fake_model import FakeModel
from dbfetch.plot import Plotter

class TestPlot( unittest.TestCase ):

    def setUp( self ):

        self.db = sql.create_engine( 'sqlite:///' )
        self.dbc = self.db.connect()

        Session = sessionmaker()
        Session.configure( bind=self.dbc )
        self.session = Session()

        try:
            # Can't use exist_ok for 2.7 compatibility...
            os.makedirs( './test_plots' )
        except Exception:
            pass
        self.plotter = Plotter( public_html='./test_plots' )
        self.intervals = Plotter.intervals( datetime.now() )
        self.fake = Faker()
        self.fake.add_provider( FakeModel )

        return super( TestPlot, self ).setUp()

    def tearDown( self ):

        return super( TestPlot, self ).tearDown()

    def test_plot( self ):

        schema = self.fake.schema()
        rows = []
        row_ct = 20
        timestamp_key = [c['name'] for c in schema if 'timestamp' in c][0]
        for i in range( row_ct ):
            row = self.fake.row( schema )
            row[timestamp_key] = datetime.now() - timedelta( hours=(row_ct - i) )
            rows.append( row )
        indexes = {c['name']: c['index_as'] for c in schema if 'index_as' in c}

        for plot in self.plotter.plot_location(
            'day',
            timestamp_key,
            rows,
            indexes,
            multi=False,
            output='test-plot',
            title='Test Plot'
        ):

            self.assertListEqual(
                plot.data,
                [r[plot.index] for r in rows]
            )
            self.assertListEqual(
                plot.times,
                [r[timestamp_key] for r in rows]
            )
            self.assertEqual(
                plot.title,
                'Test Plot ' + indexes[plot.index]
            )
            self.assertEqual(
                plot.filename,
                'test-plot-' + plot.index.replace( '_', '-' ) + '-day.png'
            )

            plot.plot()
            plot.save()
            plot.close()

    def test_plot_multi( self ):

        schema = self.fake.schema()
        rows = []
        row_ct = 20
        for i in range( row_ct ):
            row = self.fake.row( schema )
            row['timestamp'] = datetime.now() - timedelta( hours=(row_ct - i) )
            rows.append( row )
        indexes = {c['name']: c['index_as'] for c in schema if 'index_as' in c}
        timestamp_name = [c['name'] for c in schema if 'timestamp' in c][0]

        for plot in self.plotter.plot_location(
            'day',
            timestamp_name,
            rows,
            indexes,
            multi=True,
            output='test-multi-plot',
            title='Test Multi Plot'
        ):

            self.assertTrue( isinstance( plot, Plotter.MultiPlot ) )

            idx = ''
            for idx in indexes:
                self.assertListEqual(
                    plot.data[idx],
                    [r[idx] for r in rows]
                )
                self.assertListEqual(
                    plot.times[idx],
                    [r[timestamp_name] for r in rows]
                )
            self.assertEqual(
                plot.title,
                'Test Multi Plot'
            )
            self.assertEqual(
                plot.filename,
                'test-multi-plot-' + idx.replace( '_', '-' ) + '-day.png'
            )

            plot.plot()
            plot.save()

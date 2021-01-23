
from __future__ import division
import requests
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
import matplotlib
matplotlib.use( 'Agg' )
matplotlib.rc( 'font', family='monospace', weight='bold', size='6' )
from matplotlib import pyplot
from matplotlib.dates import HourLocator, DateFormatter, DayLocator, MonthLocator

class Plotter( object ):

    dpi = 100

    def __init__( self, title, x_loc=None, x_form=None, w=300, h=180 ):

        self._w = w / self.dpi
        self._h = h / self.dpi

        self._plots = 0

        self.fig, self.ax = pyplot.subplots()
        self.fig.suptitle( title )
        self.fig.set_figheight( self._h )
        self.fig.set_figwidth( self._w )
        if x_loc:
            self.ax.xaxis.set_major_locator( x_loc )
        if x_form:
            self.ax.xaxis.set_major_formatter( x_form )

        pyplot.grid( True )

    def plot( self, x, y, label=None ):
        if label:
            self.ax.plot( x, y, label=label )
        else:
            self.ax.plot( x, y )

        self._plots += 1
        if 1 < self._plots:
            self.ax.legend()

        self.fig.tight_layout()

        #pyplot.xticks( rotation=35 )

    def save( self, out_path ):
        pyplot.savefig( out_path )

    @staticmethod
    def week_locator( now ):
        week_ticks = []
        tick_pos = now
        while tick_pos >= now - timedelta( days=7 ):
            week_ticks.append( tick_pos.day )
            tick_pos -= timedelta( days=1 )
        return week_ticks

    @staticmethod
    def hour_locator( now ):
        hour_ticks = []
        tick_pos = now
        while tick_pos >= now - timedelta( days=1 ):
            hour_ticks.append( tick_pos.hour )
            tick_pos -= timedelta( hours=6 )
        return hour_ticks

    @staticmethod
    def intervals( now ):
        return {
            'day': {
                'start': now - timedelta( days=1 ),
                'locator': HourLocator( byhour=Plotter.hour_locator( now ) ),
                'formatter': DateFormatter( '%H:%M' ),
                'width': 300,
            },
            'week': {
                'start': now - timedelta( days=7 ),
                'locator': DayLocator( bymonthday=Plotter.week_locator( now ) ),
                'formatter': DateFormatter( '%d' ),
                'width': 300,
            },
            'month': {
                'start': now - timedelta( weeks=4 ),
                'locator': DayLocator( interval=2 ),
                'formatter': DateFormatter( '%d' ),
                'width': 500,
            },
            'year': {
                'start': now - timedelta( days=365 ),
                'locator': MonthLocator( bymonthday=1, interval=1 ),
                'formatter': DateFormatter( '%m/%d' ),
                'width': 500,
            },
        }

class Requester( object ):

    def __init__( self, db, modifiers ):
        self.db = db
        self.modifiers = modifiers
        Session = sessionmaker()
        Session.configure( bind=db )
        self.session = Session()

    def request( self, url ):
        r = requests.get( url )
        self.json = r.json()

    @staticmethod
    def format_date( date_str ):
        return datetime.strptime(
            date_str.replace( 'Z', '' ), '%Y-%m-%dT%H:%M:%S.%f' )

    def _format_json_obj( self, json_obj ):
        for key in json_obj:
            if key in self.modifiers:
                json_obj[key] = self.modifiers[key]( json_obj[key] )

        return json_obj

    def format_json( self ):
        if isinstance( self.json, list ):
            for json_obj in self.json:
                json_obj = self._format_json_obj( json_obj )
                yield json_obj
        else:
            json_obj = self._format_json_obj( self.json )
            yield json_obj

    def store( self, json_obj, model, filter_col, **criteria ):
        logger = logging.getLogger( 'requester.store' )
        logger.debug( 'checking for {} in {}...'.format(
            criteria, filter_col ) )
        if not self.session.query( filter_col ) \
        .filter_by( **criteria ).scalar():
            logger.debug( 'not found, adding...' )
            db_row = model( **json_obj )
            self.session.add( db_row )

    def commit( self ):
        self.session.commit()


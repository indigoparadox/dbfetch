
from __future__ import division
import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
import matplotlib
matplotlib.use( 'Agg' )
matplotlib.rc( 'font', family='monospace', weight='bold', size='6' )
from matplotlib import pyplot

class Plotter( object ):

    dpi = 100

    def __init__( self, title, x_loc=None, x_form=None, w=300, h=180 ):

        self._w = w / self.dpi
        self._h = h / self.dpi

        self.fig, self.ax = pyplot.subplots()
        self.fig.suptitle( title )
        self.fig.set_figheight( self._h )
        self.fig.set_figwidth( self._w )
        if x_loc:
            self.ax.xaxis.set_major_locator( x_loc )
        if x_form:
            self.ax.xaxis.set_major_formatter( x_form )

        pyplot.grid( True )

    def plot( self, x, y ):
        self.ax.plot( x, y )
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
        if not self.session.query( filter_col ).filter_by( **criteria ).scalar():
            db_row = model( **json_obj )
            self.session.add( db_row )

    def commit( self ):
        self.session.commit()


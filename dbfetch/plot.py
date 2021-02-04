
from __future__ import division
import matplotlib
matplotlib.use( 'Agg' )
matplotlib.rc( 'font', family='monospace', weight='bold', size='6' )
from matplotlib import pyplot
from matplotlib.dates import HourLocator, DateFormatter, DayLocator, MonthLocator
from datetime import datetime, timedelta

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



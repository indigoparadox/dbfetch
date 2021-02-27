
from __future__ import division
import logging
import os
from datetime import datetime, timedelta
import matplotlib
matplotlib.use( 'Agg' )
matplotlib.rc( 'font', family='monospace', weight='bold', size='6' )
from matplotlib import pyplot
from matplotlib.dates import HourLocator, DateFormatter, DayLocator, MonthLocator

class Plotter( object ):

    class Plot( object ):

        def __init__( self, plotter, interval, **kwargs ):

            self.dpi = int( kwargs['dpi'] ) if 'dpi' in kwargs else 100

            self._width = int( kwargs['width'] ) / self.dpi \
                if 'width' in kwargs else 300 / self.dpi
            self._height = int( kwargs['height'] ) / self.dpi \
                if 'height' in kwargs else 180 / self.dpi

            self.tz_offset = int( kwargs['tz_offset'] ) if 'tz_offset' in \
                kwargs else 0

            self.times = []
            self.data = []

            self.interval = interval
            self.filename = None
            self.plotter = plotter

            self.index = None

            self.fig, self.ax = pyplot.subplots()
            self.fig.set_figheight( self._height )
            self.fig.set_figwidth( self._width )

            interval_data = Plotter.intervals( datetime.now() )[interval]

            self.ax.xaxis.set_major_locator( interval_data['locator'] )
            self.ax.xaxis.set_major_formatter( interval_data['formatter'] )

            pyplot.grid( True )

            self._title = ''

        @property
        def title( self ):
            return self._title

        @title.setter
        def title( self, value ):
            self._title = value
            self.fig.suptitle( value )

        def set_plot_data( self, rows, time_column_name, data_column_name ):

            self.index = data_column_name

            # Timezone intervention.
            self.times = [r[time_column_name] + \
                timedelta( hours=self.tz_offset ) for r in rows]
            self.data = [r[data_column_name] for r in rows]

        def plot( self ):
            self.ax.plot( self.times, self.data )
            self.fig.tight_layout()
            #pyplot.xticks( rotation=35 )

        def save( self ):
            out_path = os.path.join(
                self.plotter.public_html, self.filename )
            pyplot.savefig( out_path )

    class MultiPlot( Plot ):

        ''' A special plot with multiple datasets. '''

        def __init__( self, plotter, title, interval, **kwargs ):
            super( Plotter.MultiPlot, self ).__init__(
                plotter, interval, **kwargs )

            # Indexed by column names.
            self.times = {}
            self.data = {}
            self.labels = {}
            self.index = []

        def set_plot_data( self, rows, t_column_name, d_column_name, label, idx ):

            self.index.append( d_column_name )

            # Timezone intervention.
            self.times[idx] = [t[t_column_name] + \
                timedelta( hours=self.tz_offset ) for t in rows]
            self.data[idx] = [d[d_column_name] for d in rows]
            self.labels[idx] = label

        def plot( self ):
            for idx in self.index:
                assert( idx in self.data )
                assert( idx in self.times )
                assert( idx in self.labels )
                self.ax.plot(
                    self.times[idx], self.data[idx], label=self.labels[idx] )
            self.ax.legend()
            self.fig.tight_layout()

    def __init__( self, **kwargs ):

        ''' A factory for creating plots. '''

        self.public_html = kwargs['public_html'] if 'public_html' in kwargs \
            else '/tmp'

        self.logger = logging.getLogger( 'plot' )

        self.kwargs = kwargs

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

    def plot_location( self, inter, t_col_nm, rows, idxs, **kwargs ):

        plot = None # Initalize for scope.
        multi = False
        output = kwargs['output'] if 'output' in kwargs else ''
        title = kwargs['title'] if 'title' in kwargs else ''

        if 'multi' in kwargs and kwargs['multi']:
            plot = Plotter.MultiPlot( self, title, inter )
            multi = True

        for idx in idxs:

            if not multi:
                plot = Plotter.Plot( self, inter )

            # Indexes should be a dict of column_name=label.
            plot_args = [rows, t_col_nm, idx]
            if multi:
                plot_args.append( idxs[idx] )
                plot_args.append( idx )
            plot.set_plot_data( *plot_args )
            plot.filename = '{}{}-{}.png'.format(
                output + '-' if output else '', idx, inter )

            if not multi:
                if title:
                    plot.title = '{} {}'.format( title, idxs[idx] )
                yield plot

        if multi:
            plot.title = title
            yield plot

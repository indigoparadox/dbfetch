
from __future__ import division
import logging
import os
import sqlalchemy as sql
from sqlalchemy.orm import sessionmaker
from ConfigParser import RawConfigParser, NoSectionError, NoOptionError
import matplotlib
matplotlib.use( 'Agg' )
matplotlib.rc( 'font', family='monospace', weight='bold', size='6' )
from matplotlib import pyplot
from matplotlib.dates import HourLocator, DateFormatter, DayLocator, MonthLocator
from datetime import datetime, timedelta
from .model import import_model

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

    def _plot( self, x, y, label=None ):
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

    @staticmethod
    def plot_mod( module_key, module, args, config, session, combined=False ):
        logger = logging.getLogger( 'plot.combined' )

        now = datetime.now()
        intervals = Plotter.intervals( now )
        indexes = module['indexes']
        timestamp = getattr( module['model'], module['timestamp'] )

        l_cfg_key = None
        for loc in config.get( module_key, 'locations' ).split( ',' ):
            l_cfg_key = '{}-location-{}'.format( module_key, loc )
            tz_offset = 0
            plot = None # Initalize for scope.
            title = None # Initalize for scope.
            last_idx = None # Initalize for scope.

            try:
                tz_offset = config.getint( l_cfg_key, 'tz_offset' )
                logger.debug( 'using timezone offset of %d', tz_offset )
            except NoOptionError:
                logger.debug( 'no timezone offset specified; using 0' )

            def save_plot( plot_sav, idx, interval ):
                out_path = os.path.join(
                    config.get( module_key, 'public_html' ),
                    '{}-{}-{}.png'.format(
                        config.get( l_cfg_key, 'output' ), idx, interval ) )
                plot_sav.save( out_path )

            for inter in intervals:

                if combined:
                    # Prepare the title for the whole plot.
                    title = '{} {}'.format( config.get( l_cfg_key, 'title' ),
                        module['title'] )

                    plot = Plotter(
                        title, intervals[inter]['locator'], intervals[inter]['formatter'],
                        w=intervals[inter]['width'] )

                for idx in indexes:
                    times = []
                    data = []
                    for row in session.query( timestamp, indexes[idx]['field'] ) \
                    .filter( timestamp >= intervals[inter]['start'] ):
                        # Timezone intervention.
                        times.append( row[0] + timedelta( hours=tz_offset ) )
                        data.append( row[1] )

                    if combined:
                        # Just plot, save the combined plot later.
                        plot._plot( times, data, label=indexes[idx]['label'] )

                    else:
                        # Plot and save.
                        title = '{} {}'.format( config.get( l_cfg_key, 'title' ),
                            indexes[idx]['title'] )

                        plot = Plotter(
                            title, intervals[inter]['locator'],
                            intervals[inter]['formatter'],
                            w=intervals[inter]['width'] )

                        plot._plot( times, data )

                        save_plot( plot, idx, inter )

                    last_idx = idx

                if combined:
                    save_plot( plot, last_idx, inter )

    @staticmethod
    def plot_chart( args, config ):

        # Run each requested module.
        for module_key in args.modules.split( ',' ):

            eng = sql.create_engine( config.get( module_key, 'connection' ) )
            with eng.connect() as dbc:

                module = import_model( module_key, dbc, args.models )

                session_proto = sessionmaker()
                session_proto.configure( bind=dbc )
                session = session_proto()

                # Try to setup and run the module.
                Plotter.plot_mod( module_key, module, args, config, session,
                    combined=('combined' == module['index_plot']) )

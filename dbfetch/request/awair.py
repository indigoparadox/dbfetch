
import logging
import sqlalchemy as sql
from dbfetch.request import Requester
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

BaseAwair = declarative_base()

class AwairModel( BaseAwair ):
    __tablename__ = 'awair'

    location = sql.Column( sql.Integer, primary_key=True )
    timestamp = sql.Column( sql.DateTime, primary_key=True )
    score = sql.Column( sql.Integer )
    dew_point = sql.Column( sql.Float )
    temp = sql.Column( sql.Float )
    humid = sql.Column( sql.Float )
    abs_humid = sql.Column( sql.Float )
    co2 = sql.Column( sql.Float )
    co2_est = sql.Column( sql.Float )
    voc = sql.Column( sql.Float )
    voc_baseline = sql.Column( sql.Float )
    voc_h2_raw = sql.Column( sql.Float )
    voc_ethanol_raw = sql.Column( sql.Float )
    pm25 = sql.Column( sql.Float )
    pm10_est = sql.Column( sql.Float )

    @staticmethod
    def create_all( db ):
        BaseAwair.metadata.create_all( db )

class ModelRequester( Requester ):

    def __init__( self, db, config ):
        self.logger = logging.getLogger( 'requester.awair' )

        self.config = config

        self.logger.debug( 'ensuring schema...' )
        AwairModel.create_all( db )

        super( ModelRequester, self ).__init__( db, {
            'timestamp': lambda o: Requester.format_date( o ),
        } )

    def fetch( self ):

        locations = self.config.get( 'awair', 'locations' ).split( ',' )
        for l in locations:
            self.logger.debug( 'checking location: {}...'.format( l ) )
            json = Requester.request(
                self.config.get( 'awair-location-{}'.format( l ), 'url' ) )
            for obj in self.format_json( json ):
                obj['location'] = l
                self.store(
                    obj, AwairModel, AwairModel.timestamp,
                    timestamp=obj['timestamp'] )

            self.commit()


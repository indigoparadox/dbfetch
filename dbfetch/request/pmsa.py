
import logging
import sqlalchemy as sql
from dbfetch.request import Requester
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

BasePMSA = declarative_base()

class PMSAModel( BasePMSA ):
    __tablename__ = 'pmsa'

    location = sql.Column( sql.Integer, primary_key=True )
    timestamp = sql.Column( sql.DateTime, primary_key=True )
    pm10_standard = sql.Column( sql.Integer )
    pm25_standard = sql.Column( sql.Integer )
    pm100_standard = sql.Column( sql.Integer )
    pm10_env = sql.Column( sql.Integer )
    pm25_env = sql.Column( sql.Integer )
    pm100_env = sql.Column( sql.Integer )
    particles_03um = sql.Column( sql.Integer )
    particles_05um = sql.Column( sql.Integer )
    particles_10um = sql.Column( sql.Integer )
    particles_25um = sql.Column( sql.Integer )
    particles_50um = sql.Column( sql.Integer )
    particles_100um = sql.Column( sql.Integer )
    tvoc = sql.Column( sql.Integer )
    humidity = sql.Column( sql.Integer )
    temperature = sql.Column( sql.Integer )
    eco2 = sql.Column( sql.Integer )

    @staticmethod
    def create_all( db ):
        BasePMSA.metadata.create_all( db )

class ModelRequester( Requester ):

    def __init__( self, db, config ):
        self.logger = logging.getLogger( 'requester.pmsa' )

        self.config = config

        self.logger.debug( 'ensuring schema...' )
        PMSAModel.create_all( db )

        super( ModelRequester, self ).__init__( db, {
            'timestamp': lambda o: datetime.fromtimestamp( int( o ) )
        } )

    def fetch( self ):

        locations = self.config.get( 'pmsa', 'locations' ).split( ',' )
        for l in locations:
            self.logger.debug( 'checking location: {}...'.format( l ) )
            json = Requester.request(
                self.config.get( 'pmsa-location-{}'.format( l ), 'url' ) )
            for obj in self.format_json( json ):
                obj['location'] = l
                self.store(
                    obj, PMSAModel, PMSAModel.timestamp,
                    timestamp=obj['timestamp'] )

            self.commit()


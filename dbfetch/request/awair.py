
import logging
from dbfetch.request import Requester
from dbfetch.models.awair import AwairModel
from datetime import datetime

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



import logging
from datetime import datetime

__requester__ = 'PMSARequester'

class PMSARequester( Requester ):

    def __init__( self, db, model ):
        super().__init__( db, {
            'timestamp': lambda o: datetime.fromtimestamp( int( o ) )
        } )
        self.model = model

    def run( self, config ):

        logger = logging.getLogger( 'requester.pmsa' )

        locations = config.get( 'pmsa', 'locations' ).split( ',' )
        for l in locations:
            logger.debug( 'checking location: {}...'.format( l ) )
            json = Requester.request(
                config.get( 'pmsa-location-{}'.format( l ), 'url' ) )
            for obj in self.format_json( json ):
                obj['location'] = l
                r.store( obj, PMSA, PMSA.timestamp, timestamp=obj['timestamp'] )

            r.commit()


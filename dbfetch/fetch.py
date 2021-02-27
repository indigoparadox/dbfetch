
import logging
import requests

class Fetcher( object ):

    def __init__( self ):

        self.logger = logging.getLogger( 'fetch' )

    def fetch_location( self, url, location ):

        # TODO: Handle authentication.

        self.logger.debug( 'checking location: %s...', location )
        json_data= requests.get( url ).json()
        if isinstance( json_data, list ):
            for obj in json_data:
                obj['location'] = location
                yield obj
        else:
            json_data['location'] = location
            yield json_data

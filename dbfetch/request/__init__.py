
import logging
import requests
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

class Requester( object ):

    def __init__( self, db, modifiers ):
        self.db = db
        self.modifiers = modifiers
        Session = sessionmaker()
        Session.configure( bind=db )
        self.session = Session()

    @staticmethod
    def request( url ):
        r = requests.get( url )
        return r.json()

    @staticmethod
    def format_date( date_str ):
        return datetime.strptime(
            date_str.replace( 'Z', '' ), '%Y-%m-%dT%H:%M:%S.%f' )

    def _format_json_obj( self, json_obj ):
        logger = logging.getLogger( 'request.json' )
        for key in json_obj:
            if key in self.modifiers:
                logger.debug( 'replacing {} with {}'.format(
                    json_obj[key], self.modifiers[key]( json_obj[key] ) ) )
                json_obj[key] = self.modifiers[key]( json_obj[key] )

        return json_obj

    def format_json( self, json ):
        if isinstance( json, list ):
            for json_obj in json:
                json_obj = self._format_json_obj( json_obj )
                yield json_obj
        else:
            json_obj = self._format_json_obj( json )
            yield json_obj

    def store( self, json_obj, model, filter_col, **criteria ):
        logger = logging.getLogger( 'request.store' )
        logger.debug( 'checking for {} in {}...'.format(
            criteria, filter_col ) )
        if not self.session.query( filter_col ) \
        .filter_by( **criteria ).scalar():
            logger.debug( 'storing new data: {}'.format( json_obj ) )
            db_row = model( **json_obj )
            self.session.add( db_row )

    def commit( self ):
        self.session.commit()


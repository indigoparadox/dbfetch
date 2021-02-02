
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
        logger = logging.getLogger( 'requester.store' )
        logger.debug( 'checking for {} in {}...'.format(
            criteria, filter_col ) )
        if not self.session.query( filter_col ) \
        .filter_by( **criteria ).scalar():
            logger.debug( 'not found, adding...' )
            db_row = model( **json_obj )
            self.session.add( db_row )

    def commit( self ):
        self.session.commit()


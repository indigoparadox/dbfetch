
import logging
import requests
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import pprint

class Requester( object ):

    class ReiterException( Exception ):
        pass

    def __init__( self, db, modifiers, fields, options ):
        self.db = db
        self.fields = fields
        self.modifiers = modifiers
        Session = sessionmaker()
        Session.configure( bind=db )
        self.session = Session()
        self.delete_undef = \
            options['delete_undef'] if 'delete_undef' in options else False

    @staticmethod
    def request( url ):
        r = requests.get( url )
        return r.json()

    @staticmethod
    def format_date( obj, key ):
        logger = logging.getLogger( 'request.date' )
        logger.debug( 'formatting date: %s', obj[key] )
        return datetime.strptime(
            obj[key].replace( 'Z', '' ), '%Y-%m-%dT%H:%M:%S.%f' )
    
    @staticmethod
    def format_flatten( obj, key ):
        
        ''' Given a nested object, transform it into a group of keys with the
        old key appended to the keys of the inner keys. '''

        logger = logging.getLogger( 'request.flatten' )

        #if isinstance( obj[key], object ):
        logger.debug( 'flattening object %s...', key )
        for iter_key in obj[key]:
            logger.debug( 'flattening %s[%s] to %s_%s...',
                key, iter_key, key, iter_key )
            obj['{}_{}'.format( key, iter_key )] = obj[key][iter_key]
        #else:
        #    logger.debug( 'not flattening non-object %s...', key )

        del obj[key]

        # Force _format_json_obj below to reiterate with new keys!
        raise Requester.ReiterException

    def _format_json_obj( self, json_obj ):
        
        ''' Apply transformations to data fields. '''

        logger = logging.getLogger( 'request.json' )

        need_iter_keys = True

        while need_iter_keys:
            logger.debug( 'iterating keys...' )
            try:
                # Iterate through keys... use .keys() here to avoid a runtime
                # error in 2.x.
                for key in json_obj.keys():
                    if key in self.modifiers:
                        logger.debug( 'replacing %s (%s) using %s',
                            key, json_obj[key], self.modifiers[key] )
                        json_obj[key] = self.modifiers[key]( json_obj, key )

                # We've iterated through the keys without triggering a re-iter!
                logger.debug( 'iteration complete!' )
                need_iter_keys = False
                        
            except Requester.ReiterException:
                logger.debug( 'reiteration triggered!' )
                pass

        if self.delete_undef:
            for key in json_obj.keys():
                if not key in self.fields:
                    del json_obj[key]

        pprint.pprint( json_obj )

        return json_obj

    def format_json( self, json ):
        if isinstance( json, list ):
            # Apply the transformations to every object in the list.
            for json_obj in json:
                json_obj = self._format_json_obj( json_obj )
                yield json_obj
        else:
            # Only one object returned.
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


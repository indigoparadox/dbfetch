
import logging
import sqlalchemy as sql
from .request import Requester
from .model import import_model

def fetch_mod( module_key, module, args, config, dbc ):

    logger = logging.getLogger( 'fetch.{}'.format( module_key ) )

    locations = config.get( module_key, 'locations' ).split( ',' )
    for loc in locations:
        logger.debug( 'checking location: %s...', loc )
        req = Requester( dbc, module['transformations'] )
        json = Requester.request(
            config.get( '{}-location-{}'.format(
                module_key, loc ), 'url' ) )
        for obj in req.format_json( json ):
            obj['location'] = loc
            criteria = {module['timestamp']: obj[module['timestamp']]}
            req.store(
                obj, module['model'],
                getattr( module['model'], module['timestamp'] ),
                **criteria )

        req.commit()

def fetch( args, config ):

    logger = logging.getLogger( 'fetch' )

    # Run each requested module.
    for module_key in args.modules.split( ',' ):

        try:
            eng = sql.create_engine( config.get( module_key, 'connection' ) )
            with eng.connect() as dbc:

                module = import_model( module_key, dbc, args.models )

                fetch_mod( module_key, module, args, config, dbc )

        except Exception as e:
            logger.error( 'failed to execute module %s: %s', module_key, e )

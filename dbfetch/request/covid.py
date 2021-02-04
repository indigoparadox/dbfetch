
import logging
import sqlalchemy as sql
from dbfetch.request import Requester
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

BaseCOVID = declarative_base()

class COVIDModel( BaseCOVID ):
    __tablename__ = 'covid'
    
    test_date = sql.Column( sql.DateTime, primary_key=True )
    county = sql.Column( sql.String( 32 ) )
    new_positives = sql.Column( sql.Integer )
    cumulative_number_of_positives = sql.Column( sql.Integer )
    total_number_of_tests = sql.Column( sql.Integer )
    cumulative_number_of_tests = sql.Column( sql.Integer )

    @staticmethod
    def create_all( db ):
        BaseCOVID.metadata.create_all( db )

class ModelRequester( Requester ):

    def __init__( self, db, config ):
        self.logger = logging.getLogger( 'requester.covid' )

        self.config = config

        self.logger.debug( 'ensuring schema...' )
        COVIDModel.create_all( db )

        super( ModelRequester, self ).__init__( db, {
            'test_date': lambda o: Requester.format_date( o ),
        } )

    def fetch( self ):

        json = Requester.request( self.config.get( 'covid', 'url' ) )
        for obj in self.format_json( json ):
            self.store(
                obj, COVIDModel, COVIDModel.test_date,
                test_date=obj['test_date'] )

        self.commit()
 

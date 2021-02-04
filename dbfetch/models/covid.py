
import sqlalchemy as sql
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


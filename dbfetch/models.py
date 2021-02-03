
import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base

BaseCOVID = declarative_base()

class COVID( BaseCOVID ):
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

BaseAwair = declarative_base()

class Awair( BaseAwair ):
    __tablename__ = 'awair'

    location = sql.Column( sql.Integer, primary_key=True )
    timestamp = sql.Column( sql.DateTime, primary_key=True )
    score = sql.Column( sql.Integer )
    dew_point = sql.Column( sql.Float )
    temp = sql.Column( sql.Float )
    humid = sql.Column( sql.Float )
    abs_humid = sql.Column( sql.Float )
    co2 = sql.Column( sql.Float )
    co2_est = sql.Column( sql.Float )
    voc = sql.Column( sql.Float )
    voc_baseline = sql.Column( sql.Float )
    voc_h2_raw = sql.Column( sql.Float )
    voc_ethanol_raw = sql.Column( sql.Float )
    pm25 = sql.Column( sql.Float )
    pm10_est = sql.Column( sql.Float )

    @staticmethod
    def create_all( db ):
        BaseAwair.metadata.create_all( db )

BasePMSA = declarative_base()

class PMSA( BasePMSA ):
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


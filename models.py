
from sqlalchemy import Column, Integer, DateTime, String, Float
from sqlalchemy.ext.declarative import declarative_base

BaseCOVID = declarative_base()

class COVID( BaseCOVID ):
    __tablename__ = 'covid'
    
    test_date = Column( DateTime, primary_key=True )
    county = Column( String( 32 ) )
    new_positives = Column( Integer )
    cumulative_number_of_positives = Column( Integer )
    total_number_of_tests = Column( Integer )
    cumulative_number_of_tests = Column( Integer )

BaseAwair = declarative_base()

class Awair( BaseAwair ):
    __tablename__ = 'awair'

    location = Column( Integer, primary_key=True )
    timestamp = Column( DateTime, primary_key=True )
    score = Column( Integer )
    dew_point = Column( Float )
    temp = Column( Float )
    humid = Column( Float )
    abs_humid = Column( Float )
    co2 = Column( Float )
    co2_est = Column( Float )
    voc = Column( Float )
    voc_baseline = Column( Float )
    voc_h2_raw = Column( Float )
    voc_ethanol_raw = Column( Float )
    pm25 = Column( Float )
    pm10_est = Column( Float )

BasePMSA = declarative_base()

class PMSA( BasePMSA ):
    __tablename__ = 'pmsa'

    location = Column( Integer, primary_key=True )
    timestamp = Column( DateTime, primary_key=True )
    pm10_standard = Column( Integer )
    pm25_standard = Column( Integer )
    pm100_standard = Column( Integer )
    pm10_env = Column( Integer )
    pm25_env = Column( Integer )
    pm100_env = Column( Integer )
    particles_03um = Column( Integer )
    particles_05um = Column( Integer )
    particles_10um = Column( Integer )
    particles_25um = Column( Integer )
    particles_50um = Column( Integer )
    particles_100um = Column( Integer )
    tvoc = Column( Integer )
    humidity = Column( Integer )
    temperature = Column( Integer )
    eco2 = Column( Integer )

def create_covid( db ):
    BaseCOVID.metadata.create_all( db )

def create_awair( db ):
    BaseAwair.metadata.create_all( db )

def create_pmsa( db ):
    BasePMSA.metadata.create_all( db )


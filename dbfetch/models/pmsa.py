
import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base

BasePMSA = declarative_base()

class PMSAModel( BasePMSA ):
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



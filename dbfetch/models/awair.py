
import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base

BaseAwair = declarative_base()

class AwairModel( BaseAwair ):
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



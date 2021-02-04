
import logging
from dbfetch.request import Requester
from dbfetch.models.pmsa import PMSAModel
from datetime import datetime

class ModelRequester( Requester ):

    model = PMSAModel
    timestamp_key = 'timestamp'
    transformations = {
        'timestamp': lambda o: datetime.fromtimestamp( int( o ) )
    }


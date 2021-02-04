
from dbfetch.request import Requester
from dbfetch.models.covid import COVIDModel

class ModelRequester( Requester ):

    model = COVIDModel
    timestamp_key = 'test_date'
    transformations = {
        'test_date': lambda o: Requester.format_date( o ),
    }


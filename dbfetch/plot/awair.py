
import logging
from dbfetch.plot import Plotter
from dbfetch.models.awair import AwairModel

class ModelPlotter( Plotter ):

    index_plot = 'single'
    indexes = {
        'co2': {
            'field': AwairModel.co2,
            'title': 'CO2',
        },
        'voc': {
            'field': AwairModel.voc,
            'title': 'VOC',
        },
        'pm25': {
            'field': AwairModel.pm25,
            'title': 'Particles < 2.5um',
        },
    }
    timestamp = AwairModel.timestamp




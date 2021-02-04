
import logging
from dbfetch.plot import Plotter
from dbfetch.models.pmsa import PMSAModel

class ModelPlotter( Plotter ):

    index_plot = 'single'
    indexes = {
        #'co2': {
        #    'field': PMSAModel.co2,
        #    'title': 'CO2',
        #},
        'voc': {
            'field': PMSAModel.tvoc,
            'title': 'TVOC',
        },
        'pm25': {
            'field': PMSAModel.particles_25um,
            'title': 'Particles < 2.5um',
        },
    }
    timestamp = PMSAModel.timestamp


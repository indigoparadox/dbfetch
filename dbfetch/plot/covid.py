
import logging
from dbfetch.plot import Plotter
from dbfetch.models.covid import COVIDModel

class ModelPlotter( Plotter ):

    index_plot = 'combined'
    title = 'COVID-19 New Positive Tests'
    indexes = {
        'new_positives': {
            'field': COVIDModel.new_positives,
            'label': 'New Positives',
        },
        'total_number_of_tests': {
            'field': COVIDModel.total_number_of_tests,
            'label': 'Total Tests',
        },
    }
    timestamp = COVIDModel.test_date


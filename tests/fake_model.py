
import random
import string
import time
from datetime import date, datetime

from faker.providers import BaseProvider

class FakeModel( BaseProvider ):

    def sql_type( self, number ):
        num_types = ['int', 'float']
        return random.choice( num_types ) if number else 'string'

    def column_name( self ):
        names_start = ['eco2', 'tvoc', 'tests', 'cities', 'pm25', 'co2',
            'voc', 'pm10']
        names_end = ['per_capita', 'to_date', 'per_mm2', 'per_year',
            'per_month', 'per_day']
        return '{}_{}'.format(
            random.choice( names_start ), random.choice( names_end ) )

    def int_transformation( self ):
        transformations = ['int', 'math.sqrt', 'float']
        return random.choice( transformations )

    def field_def( self, primary_key=False, transforms=False, number=False ):
        field_out = {
            'name': self.column_name(),
            'type': self.sql_type( number )
        }

        if primary_key:
            field_out['primary_key'] = True
        else:
            field_out['nullable'] = True

        if 'string' == field_out['type']:
            field_out['sz'] = str( random.randint( 64, 255 ) )
        elif 'int' == field_out['type'] and transforms:
            if 50 > random.randint( 0, 300 ):
                field_out['transformations'] = []
                for i in range( random.randint( 3, 6 ) ):
                    field_out['transformations'].append(
                        self.int_transformation() )

        return field_out

    def schema( self, timestamp_str=False, field_ct=3 ):
        fields = []
        while field_ct > len( fields ):
            fake_field = self.field_def( number=(0 == len( fields ) % 2) )
            if 0 == len( fields ) % 2:
                fake_field['index_as'] = fake_field['name'].upper()
            if fake_field['name'] not in [f['name'] for f in fields]:
                fields.append( fake_field )

        fields.insert( 0, {
            'name': 'timestamp',
            'primary_key': True,
            'type': 'datetime',
            'timestamp': True,
            'transformations': [
                'ModelTransforms.str_date_no_z'
            ] if timestamp_str else [
                'int',
                'datetime.fromtimestamp'
            ]
        } )

        fields.insert( 0, {
            'name': 'key',
            'primary_key': True,
            'type': 'int'
        } )

        return fields

    def field_entry( self, field_def, **kwargs ):
        fake_value = None

        datetime_as = kwargs['datetime_as'] if 'datetime_as' in kwargs \
            else 'datetime'
        timestamp = kwargs['timestamp'] if 'timestamp' in kwargs \
            else datetime.now()

        assert( datetime == type( timestamp ) )

        if 'int' == field_def['type']:
            fake_value = random.randint( 0, 1024 )
        elif 'float' == field_def['type']:
            fake_value = random.random()
        elif 'string' == field_def['type']:
            string_len = random.randint( 10, int( field_def['sz'] ) - 1 )
            fake_value = ''.join(
                [random.choice( string.ascii_letters ) \
                    for i in range( string_len )] )
        elif 'datetime' == field_def['type']:
            if 'datetime' == datetime_as:
                fake_value = timestamp
            elif 'string' == datetime_as:
                fake_value = \
                    datetime.strftime( timestamp, '%Y-%m-%dTZ%H:%M:%S.%f' )
            elif 'int' == datetime_as:
                if hasattr( timestamp, 'timestamp' ):
                    fake_value = int( timestamp.timestamp() )
                else:
                    print( 'falling back to datetime diff' )
                    fake_value = \
                        int( (timestamp - datetime( 1970, 1, 1 )).total_seconds() )
            elif 'float' == datetime_as:
                if hasattr( timestamp, 'timestamp' ):
                    fake_value = float( timestamp.timestamp() )
                else:
                    print( 'falling back to datetime diff' )
                    fake_value = float(
                        (timestamp - datetime( 1970, 1, 1 )).total_seconds() )

        return fake_value

    def row( self, schema, **kwargs ):

        row = {}

        for field_def in schema:
            row[field_def['name']] = \
                self.field_entry( field_def, **kwargs )

        return row

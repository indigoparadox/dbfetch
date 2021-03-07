
import shutil
import os

def copy_examples_to( dest_path ):
    examples_src_path = os.path.dirname( os.path.abspath( __file__ ) )
    models_dest_path = os.path.join( dest_path, 'models' )
    try:
        os.mkdir( dest_path )
    except OSError:
        # Exists.
        pass
    try:
        os.mkdir( models_dest_path )
    except OSError:
        # Exists.
        pass
    for entry in os.listdir( examples_src_path ):
        entry_src_path = os.path.join( examples_src_path, entry )
        if entry.endswith( '.yml' ):
            shutil.copy( entry_src_path, models_dest_path )
        elif entry.endswith( '.dist' ):
            shutil.copy( entry_src_path, dest_path )

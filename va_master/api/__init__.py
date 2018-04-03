from os.path import dirname, basename, isfile
import glob
try: 
    from custom_modules import * 
    custom_modules = glob.glob(dirname(__file__) + '/custom_modules/*.py')
except: 
    print ('Could not import custom modules - probably just missing the file. ')
    custom_modules = []

modules = glob.glob(dirname(__file__)+"/*.py") + custom_modules 
__all__ = [basename(f)[:-3] for f in modules if isfile(f)] 
__all__ = [f for f in __all__ if f not in ['url_handler', 'handler', '__init__', 'api_test']]


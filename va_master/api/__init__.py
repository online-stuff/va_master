from os.path import dirname, basename, isfile
import glob

modules = glob.glob(dirname(__file__)+"/*.py")
__all__ = [basename(f)[:-3] for f in modules if isfile(f)] 
__all__ = [f for f in __all__ if f not in ['url_handler', 'handler', '__init__']]
print ('All is : ', __all__) 


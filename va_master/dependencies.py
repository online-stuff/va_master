import platform
import pkg_resources
import zipfile
import StringIO

def get_dependency_package():
    '''Returns a string representing the binary dep. package.'''
    platform_sys = platform.system()
    platform_arch = platform.architecture()[0]

    if platform_arch != '64bit':
        raise OSError('This platform is not supported! (64bit only)')
    if platform_sys == 'Windows':
        return 'vapour_windows_amd64'
    elif platform_sys == 'Linux':
        return 'vapour_linux_amd64'
    else:
        raise OSError('This platform is not supported!')

DEFAULT_DEP_FILE = 'bindeps.zip'

def load_file(filename):
    mod = get_dependency_package()
    dep_data = pkg_resources.resource_string(mod, DEFAULT_DEP_FILE)
    dep_file = StringIO.StringIO(dep_data)
    with zipfile.ZipFile(dep_file) as zf:
        return zf.open(filename).read()

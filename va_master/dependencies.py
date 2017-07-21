import platform
import pkg_resources
import zipfile
from six import StringIO
import os
import stat
from collections import namedtuple

DepInfo = namedtuple('DepInfo', ['package', 'extension'])

def get_dependency_info():
    '''Returns a DepInfo (dependency package and executable extension) for the
    current platform.'''
    platform_sys = platform.system()
    platform_arch = platform.architecture()[0]

    if platform_arch != '64bit':
        raise OSError('This platform is not supported! (64bit only)')
    if platform_sys == 'Windows':
        return DepInfo('vapour_windows_amd64', '.exe')
    elif platform_sys == 'Linux':
        return DepInfo('vapour_linux_amd64', '.bin')
    else:
        raise OSError('This platform is not supported!')

DEFAULT_DEP_FILE = 'bindeps.zip'

def load_file(filename, dep_file=DEFAULT_DEP_FILE):
    dep_info = get_dependency_info()
    filename+= dep_info.extension
    dep_data = pkg_resources.resource_string(dep_info.package, dep_file)
    dep_file = StringIO(dep_data)
    with zipfile.ZipFile(dep_file) as zf:
        return zf.open(filename).read(), filename

def load_and_save(filename, path):
    bin_data, real_filename = load_file(filename)
    path = os.path.join(path, real_filename)
    with open(path, 'wb') as myfile:
        myfile.write(bin_data)
        os.fchmod(myfile.fileno(),
            stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
    return path
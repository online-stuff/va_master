import setuptools

setuptools.setup(
  name='vapourapps',
  packages=setuptools.find_packages(),
  version='1.0.0',
  description='This package contains the master server of VapourApps, a DevOps tool for corporate apps.',
  keywords=['vapourapps'],
  author='Filip Dimitrovski',
  install_requires=[
    'salt',
    'python-novaclient',
    'pbkdf2', 
    'pyVmomi', #for vmware
    'gitpython',
    'watchdog', 
    'clc-sdk',
    'google-api-python-client',
  ],
  zip_safe=False,
  entry_points = {
    'console_scripts': [
        'vapourapps = va_master.cli:entry',
    ]
  }
)

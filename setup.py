import setuptools

setuptools.setup(
  name='vapourapps',
  packages=setuptools.find_packages(),
  version='0.0.4',
  description='This package contains the master server of VapourApps, a DevOps tool for corporate apps.',
  keywords=['vapourapps'],
  author='Filip Dimitrovski',
  install_requires=[
    'tornado',
    'salt',
    'apache-libcloud',
    'python-novaclient',
    'pbkdf2'
  ],
  zip_safe=False,
  entry_points = {
    'console_scripts': [
        'vapourapps = va_master.cli:entry'
    ]
  }
)

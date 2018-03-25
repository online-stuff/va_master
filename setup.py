import setuptools

setuptools.setup(
  name='vapourapps',
  packages=setuptools.find_packages(),
  version='0.0.11',
  description='This package contains the master server of VapourApps, a DevOps tool for corporate apps.',
  keywords=['vapourapps'],
  author='Filip Dimitrovski',
  install_requires=[
    'tornado',
    'pyopenSSL',
    'salt',
    'apache-libcloud',
    'python-novaclient',
    'pbkdf2', 
    'pyVmomi', #for vmware
    'libvirt-python', #for, well, libvirt
    'boto3', #for aws
    'gitpython',
    'watchdog', 
    'clc-sdk',
    'google-api-python-client',
    'paramiko', #for ssh connections
    'reportlab', #For generating PDF files
  ],
  zip_safe=False,
  entry_points = {
    'console_scripts': [
        'vapourapps = va_master.cli:entry',
        'vapourapps-test = va_master.tests:run_tests'
    ]
  }
)

import setuptools

setuptools.setup(
<<<<<<< HEAD
  name='vapourapps',
  packages=setuptools.find_packages(),
  version='0.0.11',
  description='This package contains the master server of VapourApps, a DevOps tool for corporate apps.',
  keywords=['vapourapps'],
  author='Filip Dimitrovski',
  install_requires=[
    'tornado',
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
  ],
  zip_safe=False,
  entry_points = {
    'console_scripts': [
        'vapourapps = va_master.cli:entry',
        'vapourapps-test = va_master.tests:run_tests'
    ]
  }
=======
    name='vapourapps',
    packages=setuptools.find_packages(),
    version='1.0.1',
    description='This package contains the master server of VapourApps, a \
DevOps tool for corporate apps.',
    keywords=['vapourapps'],
    author='VapourApps',
    install_requires=[
        'pyopenssl',
        'netifaces',
        'six',
        'appdirs',
        'salt',
        'pbkdf2',
        'watchdog',
        'OpenSSL',
        'clc-sdk',
        'vapour_linux_amd64;platform_system=="Linux"',
        'vapour_windows_amd64;platform_system=="Windows"',
        'cerberus'
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'vapourapps = va_master.cli:entry',
        ]
    }
>>>>>>> cd6de5a8cd757921a2839d3b71fd58e56eccf7dd
)

import setuptools

setuptools.setup(
    name='vapourapps',
    packages=setuptools.find_packages(),
    version='1.0.1',
    description='This package contains the master server of VapourApps, a \
DevOps tool for corporate apps.',
    keywords=['vapourapps'],
    author='VapourApps',
    install_requires=[
        'six',
        'salt',
        'python-novaclient',
        'pbkdf2',
        'pyVmomi',
        'gitpython',
        'watchdog',
        'clc-sdk',
        'google-api-python-client',
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
)

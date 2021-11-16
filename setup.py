from setuptools import setup, find_packages
from recorder import __version__

setup(
    name='Elzwave Session Recorder',
    version=__version__,

    author='Christian Spaeth',
    author_email='mail@cspaeth.de',

    packages=find_packages(),
    include_package_data=True,

    zip_safe=False,
    install_requires=[
        'flask',
    ],
)

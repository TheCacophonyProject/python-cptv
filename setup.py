from setuptools import setup
from pathlib import Path


here = Path(__file__).parent
with open(str(here / 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='cptv',
    version='0.1.0',

    description='Python library for handling Cacophony Project Thermal Video (CPTV) files',
    long_description=long_description,
    url='https://github.com/TheCacophonyProject/python-cptv',

    author='The Cacophony Project',
    author_email='dev@cacophony.org.nz',
    license='Apache License 2.0',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Multimedia :: Video :: Conversion',
    ],

    keywords='video compression',

    packages=['cptv'],

    install_requires=['numpy', 'Pillow', 'opencv-python'],

    extras_require={
        'test': ['pytest'],
    },
)

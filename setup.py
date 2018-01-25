from setuptools import setup, find_packages
from setuptools.extension import Extension
from Cython.Build import cythonize

long_description = """\
This is Python package provides for quick, easy parsing for Cacophony
Project Thermal Video (CPTV) files. It works with Python 3 only.

For more details on the internals of CPTV files, see the
`specification`_.

Example usage::

    from cptv import CPTVReader


    with open(filename, "rb") as f:
        reader = CPTVReader(f)
        print(reader.timestamp)
        print(reader.x_resolution)
        print(reader.y_resolution)

        for frame in reader:
            # Do something with frame.
            # Each frame is a 2D numpy array.

.. _`specification`: https://github.com/TheCacophonyProject/go-cptv/blob/master/SPEC.md
"""

extensions = [
    Extension("cptv.bitstream", ["cptv/bitstream.pyx"]),
    Extension("cptv.reader", ["cptv/reader.pyx"]),
]

setup(
    name='cptv',
    version='0.2.0',

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
    ext_modules = cythonize(extensions),

    install_requires=['numpy', 'Pillow', 'opencv-python'],
    extras_require={
        'dev': ['Cython', 'pytest'],
    },
)

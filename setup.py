from setuptools import setup, find_packages, Extension

long_description = """\
This is Python package provides for quick, easy parsing for Cacophony
Project Thermal Video (CPTV) files. It works with Python 3 only.
"""

setup(
    name="cptv",
    version="1.0.0",
    description="Python library for handling Cacophony Project Thermal Video (CPTV) files",
    long_description=long_description,
    url="https://github.com/TheCacophonyProject/python-cptv",
    author="The Cacophony Project",
    author_email="dev@cacophony.org.nz",
    license="Apache License 2.0",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Video :: Conversion",
    ],
    keywords="video compression",
    packages=["cptv"],
    setup_requires=["setuptools>=18.0", "cython>=0.29.13"],
    ext_modules=[
        Extension("cptv.reader", ["cptv/reader.pyx"]),
        Extension("cptv.writer", ["cptv/writer.pyx"]),
        Extension("cptv.bitreader", ["cptv/bitreader.pyx"]),
        Extension("cptv.bitwriter", ["cptv/bitwriter.pyx"]),
    ],
    install_requires=["numpy"],
)

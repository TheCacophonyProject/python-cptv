# python-cptv

This is Python package provides for quick, easy parsing for Cacophony
Project Thermal Video (CPTV) files. It works with Python 3 only.

For more details on the internals of CPTV files, see the
[specification](https://github.com/TheCacophonyProject/go-cptv/blob/master/SPEC.md).

## Installation

Installation from PyPI:

```
pip install cptv
```

Installation from source:

```
pip install .
```

(`python setup.py install` won't work)


## Example Usage

```python
from cptv import CPTVReader


with open(filename, "rb") as f:
    reader = CPTVReader(f)
    print(reader.timestamp)
    print(reader.x_resolution)
    print(reader.y_resolution)

    for frame in reader:
        # Do something with frame.
        # Each frame is a 2D numpy array.

```

## License

This software is licensed under the Apache License 2.0.

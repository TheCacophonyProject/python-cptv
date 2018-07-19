# python-cptv

This is Python package provides for quick, easy parsing for Cacophony
Project Thermal Video (CPTV) files. It works with **Python 3** only.

For more details on the internals of CPTV files, see the
[specification](https://github.com/TheCacophonyProject/go-cptv/blob/master/SPEC.md).

## Installation

Installation from PyPI:

```
pip install cptv
```

Installation from source (highly recommended to use a virtualenv):

```
pip install .
```

## Example Usage

```python
from cptv import CPTVReader


with open(filename, "rb") as f:
    reader = CPTVReader(f)
    print(reader.device_name)
    print(reader.timestamp)
    print(reader.x_resolution)
    print(reader.y_resolution)

    for frame, t_offset in reader:
        # Do something with frame.
        # Each frame is a 2D numpy array.

```

## License

This software is licensed under the Apache License 2.0.

## Releases

* Update the version in setup.py and commit.
* Ensure a Python 3 virtualenv is active.
* Build the source distribution: `python setup.py sdist --formats=zip`
* Tag the release, for example: `git tag -a v0.2.1 -m "0.2.1 release"`
* Push the tag to Github, for example: `git push origin v0.2.1`
* Push the release to PyPI, for example: `twine upload dist/cptv-0.2.1.zip`

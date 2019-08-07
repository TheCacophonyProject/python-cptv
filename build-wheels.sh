#!/bin/sh

# Create Linux binary wheels for supported Python versions.
#
# The wheels are created inside a specialised Docker container and the
# wheels end up in the `wheelhouse` subdirectory.

sudo rm -rf wheelhouse

docker run --rm -e PLAT=manylinux1_x86_64 -v `pwd`:/io quay.io/pypa/manylinux1_x86_64 /io/_release/build-wheels.sh

sudo rm -rf wheelhouse/numpy*

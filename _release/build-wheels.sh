#!/bin/bash

# This script runs inside a pypa/manylinux1 Docker container and build
# Linux wheels for python-cptv.

set -e -x

# Compile wheels
for PYBIN in /opt/python/cp{35,36,37}*/bin; do
    "${PYBIN}/pip" wheel /io/ -w wheelhouse/
done

# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    auditwheel repair "$whl" --plat $PLAT -w /io/wheelhouse/
done

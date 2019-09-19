# Copyright 2019 The Cacophony Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# cython: language_level=3

import struct


cdef class BitWriter:
    """
    BitWriter takes a file like object and allows it to be written to
    various bit widths.
    """

    cdef object s

    def __init__(self, fobj):
        self.s = fobj

    cpdef close(self):
        self.s.close()

    cpdef write(self, v):
        return self.s.write(v)

    cpdef uint32(self, v):
        self.s.write(struct.pack("<L", v))

    cpdef uint64(self, v):
        self.s.write(struct.pack("<Q", v))

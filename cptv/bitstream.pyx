# Copyright 2018 The Cacophony Project
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

import struct


cdef class BitStream:
    """
    BitStream takes a file like object and allows it to be consumed at
    various bit widths
    """

    cdef object s

    def __init__(self, fobj):
        self.s = fobj

    def bytes(self, size):
        out = self.s.read(size)
        if len(out) != size:
            raise EOFError("short read. wanted {}, got {}"
                           .format(size, len(out)))
        return out

    def uint8(self):
        return ord(self.bytes(1))

    def uint32(self):
        return struct.unpack("<L", self.bytes(4))[0]

    def uint64(self):
        return struct.unpack("<Q", self.bytes(8))[0]

    def int32(self):
        return struct.unpack("<l", self.bytes(4))[0]

    def string(self, data_len):
        formatString = str(data_len) + 's'
        return struct.unpack(formatString, self.bytes(data_len))[0]

    def iter_int(self, int total_size, int bitw):
        """Return an iterator which processes the the next total_size
        bytes, generating signed integers of bitw width.
        """
        source = self.bytes(total_size)
        cdef int i = 0
        cdef long long bits = 0
        cdef int nbits = 0
        cdef long long out = 0
        while True:
            while nbits < bitw:
                bits |= source[i] << (24 - nbits)
                nbits += 8
                i += 1
            out = twos_comp(bits >> (32 - bitw) & 0xffff, bitw)
            bits = (bits << bitw) & 0xffffffff
            nbits -= bitw
            yield out


cdef inline twos_comp(int v, int width):
    """Convert the signed value with the given bit width to its two's
    complement representation.
    """
    cdef int mask = 1 << (width - 1)
    return -(v & mask) + (v & ~mask)

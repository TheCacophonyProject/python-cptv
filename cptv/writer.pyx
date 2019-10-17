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

import gzip
import math
import struct
from array import array
from datetime import datetime
from io import BytesIO
from datetime import datetime, timedelta

cimport cython
import numpy as np

from .bitwriter import BitWriter
from .frame import Frame
from .reader import Section, Field

cdef MAGIC = b"CPTV"
cdef VERSION = b"\x02"
cdef COLS = 160
cdef ROWS = 120
cdef ELEMS = COLS * ROWS


cdef class CPTVWriter:

    cdef public object timestamp
    cdef public object device_name
    cdef public float latitude
    cdef public float longitude
    cdef public int preview_secs
    cdef public int device_id
    cdef public object motion_config

    cdef object s
    cdef object comp

    def __init__(self, fileobj):
        self.timestamp = datetime.now()
        self.s = BitWriter(gzip.GzipFile(fileobj=fileobj, mode="wb"))
        self.comp = Compressor()

    def write_header(self):
        self.s.write(MAGIC + VERSION)

        fw = FieldWriter()
        fw.uint8(ord(Field.COMPRESSION), 1)
        fw.uint32(ord(Field.X_RESOLUTION), COLS)
        fw.uint32(ord(Field.Y_RESOLUTION), ROWS)

        if self.device_name:
           fw.string(ord(Field.DEVICENAME), self.device_name)

        if self.device_id:
           fw.uint32(ord(Field.DEVICEID), self.device_id)

        if not self.timestamp:
            self.timestamp = datetime.now()
        fw.timestamp(ord(Field.TIMESTAMP), self.timestamp)

        if self.latitude:
            fw.float32(ord(Field.LATITUDE), self.latitude)

        if self.longitude:
            fw.float32(ord(Field.LONGITUDE), self.longitude)

        if self.preview_secs:
            fw.uint8(ord(Field.PREVIEW_SECS), self.preview_secs)

        if self.motion_config:
           fw.string(ord(Field.MOTION_CONFIG), self.motion_config)

        fw.write(ord(Section.HEADER), self.s)

    def write_frame(self, object frame):
        bit_width, frame_buf = self.comp.next_frame(frame.pix)

        fw = FieldWriter()
        fw.uint32(ord(Field.TIME_ON), frame.time_on / timedelta(milliseconds=1))
        fw.uint32(ord(Field.LAST_FFC_TIME), frame.last_ffc_time / timedelta(milliseconds=1))
        fw.uint8(ord(Field.BIT_WIDTH), bit_width)
        fw.uint32(ord(Field.FRAME_SIZE), len(frame_buf))
        fw.write(ord(Section.FRAME), self.s)

        frame_buf.tofile(self.s)

    def close(self):
        self.s.close()


cdef class FieldWriter:

    cdef int count
    cdef object s

    def __init__(self):
        self.s = BytesIO()
        self.count = 0

    cpdef write(self, char section_type, object out):
        out.write(struct.pack("<BB", section_type, self.count))
        out.write(self.s.getbuffer())

    cpdef timestamp(self, char code, object t):
        cdef unsigned long long micros =  int(t.timestamp() * 1_000_000)
        self.uint64(code, micros)

    cpdef uint8(self, char code, unsigned char val):
        self.s.write(struct.pack("<BBB", 1, code, val))
        self.count += 1

    cpdef uint32(self, char code, unsigned long val):
        self.s.write(struct.pack("<BBL", 4, code, val))
        self.count += 1

    cpdef uint64(self, char code, unsigned long long val):
        self.s.write(struct.pack("<BBQ", 8, code, val))
        self.count += 1

    cpdef float32(self, char code, float val):
        self.s.write(struct.pack("<BBf", 4, code, val))
        self.count += 1

    cpdef string(self, char code, object val):
        self.s.write(struct.pack("<BB", len(val), code))
        self.s.write(val)
        self.count += 1


cdef class Compressor:

    cdef int[:] frame_delta
    cdef int[:] adj_delta
    cdef unsigned short[:, :] prev_pix
    cdef object out

    def __init__(self):
        self.frame_delta = np.zeros(ELEMS, dtype="int32")
        self.adj_delta = np.zeros(ELEMS - 1, dtype="int32")
        self.prev_pix = np.zeros((ROWS, COLS), dtype="uint16")
        self.out = array("B")

    @cython.boundscheck(False) # turn off bounds-checking for entire function
    @cython.wraparound(False)  # turn off negative index wrapping for entire function
    def next_frame(self, unsigned short[:, :] pix):
        cdef int x, y, inc, i

        # Generate the interframe delta.
        # The output is written in a "snaked" fashion to avoid
        # potentially greater deltas at the edges in the next stage.
        for y in range(ROWS):
            i = y * COLS
            if y & 1 == 0:
                inc = 1
            else:
                i += (COLS - 1)
                inc = -1

            for x in range(COLS):
                self.frame_delta[i] = <long>(pix[y, x]) - <long>(self.prev_pix[y, x])
                i += inc

        self.prev_pix[...] = pix

        # Now generate the adjacent "delta of deltas".
        cdef unsigned long max_delta = 0
        cdef long delta
        for i in range(ELEMS - 1):
            delta = self.frame_delta[i + 1] - self.frame_delta[i]
            self.adj_delta[i] = delta
            max_delta = max(max_delta, abs(delta))

        # How many bits required to store the largest delta?
        # Add 1 to allow for sign bit
        cdef unsigned char width = int.bit_length(max_delta) + 1

        # Reset the buffer
        del self.out[:]

        # Write out the starting frame delta value (required for reconstruction)
        self.out.extend(struct.pack("<l", self.frame_delta[0]))

        # Pack the deltas according to the bit width determined
        self.pack_bits(width, self.adj_delta)

        return width, self.out

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef pack_bits(self, int width, int[:] vals):
        cdef unsigned long bits = 0  # scratch buffer
        cdef int num_bits = 0        # number of bits in use in scratch
        cdef long d
        cdef int i

        for i in range(vals.shape[0]):
            d = vals[i]
            bits |= <unsigned long>(twos_comp(d, width) << (32 - width - num_bits))
            num_bits += width
            while num_bits >= 8:
                self.out.append(<unsigned char>(bits >> 24))
                bits <<= 8
                num_bits -= 8

        if num_bits > 0:
            self.out.append(<unsigned char>(bits >> 24))


@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline unsigned long twos_comp(long v, unsigned char width):
    """Convert the signed value with the given bit width to its two's
    complement representation.
    """
    if v >= 0:
        return v
    return (~(-v) + 1) & ((1 << width) - 1)

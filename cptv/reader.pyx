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

import datetime
import gzip

import numpy as np

from .bitstream import BitStream


class Section:
    HEADER = b'H'
    FRAME = b'F'


class Field:
    TIMESTAMP = b'T'
    X_RESOLUTION = b'X'
    Y_RESOLUTION = b'Y'
    COMPRESSION = b'C'
    DEVICENAME = b'D'
    BIT_WIDTH = b'w'
    FRAME_SIZE = b'f'
    FRAME_OFFSET = b't'


UINT32_FIELDS = {
    Field.X_RESOLUTION,
    Field.Y_RESOLUTION,
    Field.FRAME_OFFSET,
    Field.FRAME_SIZE,
    }

UINT8_FIELDS = {
    Field.COMPRESSION,
    Field.BIT_WIDTH,
    }

STRING_FIELDS = {
    Field.DEVICENAME
}

epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)


cdef class CPTVReader:
    """
    CPTVReader is a parser and decompressor for Cacophony Project
    Thermal Video (CPTV) files.

    Usage:

        reader = CPTVReader(file_object)
        print(reader.timestamp)
        print(reader.x_resolution)
        print(reader.y_resolution)

        for frame in reader:
            print(frame)  # frame is a 2D numpy array

    """

    cdef public int compression
    cdef public object timestamp
    cdef public int x_resolution
    cdef public int y_resolution
    cdef public object frame_dim
    cdef public object device_name

    cdef object s

    def __init__(self, fileobj):
        self.s = BitStream(gzip.GzipFile(fileobj=fileobj, mode="rb"))

        # check magic and version
        if self.s.bytes(4) != b"CPTV":
            raise IOError("magic not found")

        if self.s.uint8() != 1:
            raise IOError("unsupported version")

        section_type, fields = self._read_section()
        if section_type != Section.HEADER:
            raise IOError("header not found")

        self.compression = fields[Field.COMPRESSION]
        if self.compression != 1:
            raise ValueError("unsupported compression type: {}"
                             .format(self.compression))

        self.timestamp = fields[Field.TIMESTAMP]
        self.x_resolution = fields[Field.X_RESOLUTION]
        self.y_resolution = fields[Field.Y_RESOLUTION]
        self.frame_dim = (self.y_resolution, self.x_resolution)
        self.device_name = fields.get(Field.DEVICENAME, "")

    def __iter__(self):
        cdef long v
        cdef int x, y
        cdef long d
        cdef int i
        cdef int x_res

        prev_frame = np.zeros(self.frame_dim, dtype="uint16")
        frame = np.zeros(self.frame_dim, dtype="uint16")
        delta_frame = np.zeros(self.frame_dim, dtype="int32")
        x_res = self.x_resolution
        num_deltas = (x_res * self.y_resolution) - 1

        # Precompute the way we walk through the frame.
        walk_coords = []
        # offset by 1 because we will already have initial value
        for i in range(1, num_deltas+1):
            y = i // x_res
            x = i % x_res
            # Deltas are "snaked" so work backwards through every
            # second row.
            if y % 2 == 1:
                x = x_res - x - 1
            walk_coords.append((y, x))

        while True:
            try:
                section_type, fields = self._read_section()
            except EOFError:
                return
            if section_type != Section.FRAME:
                raise IOError("unexpected section: {}".format(section_type))

            v = self.s.int32()  # read starting value
            delta_frame[0][0] = v

            # ... then apply deltas

            # sub 4 to account for uint32 just read
            frame_size = fields[Field.FRAME_SIZE] - 4
            bit_width = fields[Field.BIT_WIDTH]
            deltas = self.s.iter_int(frame_size, bit_width)
            for (y, x), d in zip(walk_coords, deltas):
                v += d
                delta_frame[y][x] = v

            # Calculate the frame by applying the delta frame to the
            # previously decompressed frame.
            frame = (prev_frame + delta_frame).astype('uint16')
            yield frame, fields[Field.FRAME_OFFSET]
            prev_frame = frame

    def _read_section(self):
        section_type = self.s.bytes(1)
        field_count = self.s.uint8()
        fields = {}
        for _ in range(field_count):
            ftype, value = self._read_field()
            fields[ftype] = value
        return section_type, fields

    def _read_field(self):
        data_len = self.s.uint8()
        ftype = self.s.bytes(1)

        if ftype in UINT8_FIELDS:
            val = self.s.uint8()
        elif ftype in UINT32_FIELDS:
            val = self.s.uint32()
        elif ftype in STRING_FIELDS:
            val = self.s.string(data_len)
        elif ftype == Field.TIMESTAMP:
            micros = self.s.uint64()
            try:
                val = epoch + datetime.timedelta(microseconds=micros)
            except OverflowError:
                print("timestamp is broken - using default")
                val = epoch
        else:
            # Unknown field, just slurp up the bytes
            val = self.s.bytes(data_len)

        return ftype, val

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

from datetime import datetime, timedelta, timezone
import gzip
import logging
import struct
import numpy as np

from .frame import Frame

logger = logging.getLogger("cptv")


class Section:
    HEADER = b"H"
    FRAME = b"F"


class Field:
    # Header fields
    TIMESTAMP = b"T"
    X_RESOLUTION = b"X"
    Y_RESOLUTION = b"Y"
    COMPRESSION = b"C"
    DEVICENAME = b"D"
    DEVICEID = b"I"

    PREVIEW_SECS = b"P"
    MOTION_CONFIG = b"M"
    LATITUDE = b"L"
    LONGITUDE = b"O"

    LOC_TIMESTAMP = b"S"
    ALTITUDE = b"A"
    ACCURACY = b"U"
    FPS = b"Z"
    MODEL = b"E"
    BRAND = b"B"
    FIRMWARE = b"V"
    CAMERA_SERIAL = b"N"
    BACKGROUND_FRAME = b"g"

    # Frame fields
    BIT_WIDTH = b"w"
    FRAME_SIZE = b"f"
    TIME_ON = b"t"
    LAST_FFC_TIME = b"c"

    TEMP_C = b"a"
    LAST_FFC_TEMP_C = b"b"


TIMESTAMP_FIELDS = {Field.TIMESTAMP, Field.LOC_TIMESTAMP}

UINT32_FIELDS = {
    Field.X_RESOLUTION,
    Field.Y_RESOLUTION,
    Field.FRAME_SIZE,
    Field.TIME_ON,
    Field.LAST_FFC_TIME,
    Field.DEVICEID,
    Field.CAMERA_SERIAL,
}

UINT8_FIELDS = {
    Field.COMPRESSION,
    Field.BIT_WIDTH,
    Field.PREVIEW_SECS,
    Field.FPS,
    Field.BACKGROUND_FRAME,
}

STRING_FIELDS = {
    Field.DEVICENAME,
    Field.MOTION_CONFIG,
    Field.MODEL,
    Field.BRAND,
    Field.FIRMWARE,
}

FLOAT_FIELDS = {
    Field.LATITUDE,
    Field.LONGITUDE,
    Field.ALTITUDE,
    Field.ACCURACY,
    Field.LAST_FFC_TEMP_C,
    Field.TEMP_C,
}


epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)


class CPTVReader:
    """
    CPTVReader is a parser and decompressor for Cacophony Project
    Thermal Video (CPTV) files.

    Usage:

        reader = CPTVReader(file_object)
        print(reader.timestamp)
        print(reader.x_resolution)
        print(reader.y_resolution)

        for frame in reader:
            print(frame)  # frame.pix is a 2D numpy array

    """

    version = None
    compression = None
    timestamp = None
    x_resolution = None
    y_resolution = None
    frame_dim = None
    device_name = None
    device_id = None

    latitude = None
    longitude = None
    loc_timestamp = None
    preview_secs = None
    motion_config = None

    altitude = None
    accuracy = None
    fps = None
    model = None
    brand = None
    firmward = None
    camera_serial = None
    background_frames = None

    def __init__(self, fileobj):
        self.s = gzip.GzipFile(fileobj=fileobj, mode="rb")
        self.header = self._read_header(self.s)
        self.frame_file_offset = self.s.tell()

    def _read_header(self, s):
        # check magic
        if s.read(4) != b"CPTV":
            raise IOError("magic not found")

        # check version
        self.version = s.read(1)[0]
        if self.version not in (1, 2):
            raise IOError("unsupported version")

        section_type, fields = self._read_section(s)
        if section_type != Section.HEADER:
            raise IOError("header not found")

        self.compression = fields[Field.COMPRESSION]
        if self.compression != 1:
            raise ValueError(
                "unsupported compression type: {}".format(self.compression)
            )

        self.timestamp = fields[Field.TIMESTAMP]
        self.x_resolution = fields[Field.X_RESOLUTION]
        self.y_resolution = fields[Field.Y_RESOLUTION]
        self.frame_dim = (self.y_resolution, self.x_resolution)
        self.device_name = fields.get(Field.DEVICENAME)
        self.device_id = fields.get(Field.DEVICEID, 0)

        self.preview_secs = fields.get(Field.PREVIEW_SECS, 0)
        self.motion_config = fields.get(Field.MOTION_CONFIG)
        self.latitude = fields.get(Field.LATITUDE, 0.0)
        self.longitude = fields.get(Field.LONGITUDE, 0.0)
        self.loc_timestamp = fields.get(Field.LOC_TIMESTAMP, 0)
        self.altitude = fields.get(Field.ALTITUDE, 0)
        self.accuracy = fields.get(Field.ACCURACY, 0)
        self.fps = fields.get(Field.FPS, 0)
        self.model = fields.get(Field.MODEL)
        self.brand = fields.get(Field.BRAND)
        self.firmware = fields.get(Field.FIRMWARE)
        self.camera_serial = fields.get(Field.CAMERA_SERIAL, 0)
        self.background_frames = fields.get(Field.BACKGROUND_FRAME, 0)

    def __iter__(self):
        s = self.s
        s.seek(self.frame_file_offset)

        linear_pix = np.zeros(self.frame_dim[0] * self.frame_dim[1], dtype="h")

        while True:
            try:
                section_type, fields = self._read_section(s)
            except EOFError:
                return

            if section_type != Section.FRAME:
                raise IOError("unexpected section: {}".format(section_type))

            frame_size = fields[Field.FRAME_SIZE]
            bit_width = fields[Field.BIT_WIDTH]

            workaround_bug_in_numpy_reading_from_gzip_files = True
            if workaround_bug_in_numpy_reading_from_gzip_files:
                packed_delta = np.frombuffer(
                    self.s.read(frame_size), dtype=np.dtype("B")
                )
            else:
                packed_delta = np.fromfile(self.s, np.dtype("B"), frame_size)

            pix = self._decompress_frame(linear_pix, packed_delta, bit_width)

            if self.version >= 2:
                time_on = timedelta(milliseconds=fields.get(Field.TIME_ON, 0))
                last_ffc_time = timedelta(
                    milliseconds=fields.get(Field.LAST_FFC_TIME, 0)
                )
                temp_c = fields.get(Field.TEMP_C, 0)
                last_ffc_temp_c = fields.get(Field.LAST_FFC_TEMP_C, 0)
                background_frame = fields.get(Field.BACKGROUND_FRAME, 0) > 0
            else:
                time_on = None
                last_ffc_time = None
                temp_c = 0
                last_ffc_temp_c = 0
                background_frame = False
            yield Frame(
                pix, time_on, last_ffc_time, temp_c, last_ffc_temp_c, background_frame
            )

    def _read_section(self, s):
        section_type = s.read(1)
        if section_type == b"":
            raise EOFError("short read")
        field_count = s.read(1)[0]
        fields = {}
        for _ in range(field_count):
            ftype, value = self._read_field(s)
            fields[ftype] = value
        return section_type, fields

    def _read_field(self, s):
        data_len = s.read(1)[0]
        ftype = s.read(1)

        if ftype in UINT8_FIELDS:
            val = self._read_uint8(s)
        elif ftype in UINT32_FIELDS:
            val = self._read_uint32(s)
        elif ftype in STRING_FIELDS:
            val = self._read_string(s, data_len)
        elif ftype in FLOAT_FIELDS:
            val = self._read_float32(s)
        elif ftype in TIMESTAMP_FIELDS:
            micros = self._read_uint64(s)
            try:
                val = epoch + timedelta(microseconds=micros)
            except OverflowError:
                print("timestamp is broken - using default")
                val = epoch
        else:
            # Unknown field, just slurp up the bytes
            logger.warn("unknown field: %s (skipping)", ftype)
            val = s.read(data_len)

        return ftype, val

    def _read_uint8(self, s):
        return s.read(1)[0]

    def _read_uint16(self, s):
        return struct.unpack("<H", s.read(2))[0]

    def _read_int32(self, s):
        return struct.unpack("<i", s.read(4))[0]

    def _read_uint32(self, s):
        return struct.unpack("<I", s.read(4))[0]

    def _read_uint64(self, s):
        return struct.unpack("<Q", s.read(8))[0]

    def _read_float32(self, s):
        return struct.unpack("<f", s.read(4))[0]

    def _read_string(self, s, length):
        return s.read(length)

    def _decompress_frame(self, current_frame, source, packed_bit_width):
        s = np.empty(self.x_resolution * self.y_resolution, dtype="h")
        s[0] = struct.unpack("<i", source[0:4])[0]  # starting value, signed

        if packed_bit_width > 16:
            raise IOError("Higher than 16bit thermal imaging not supported")

        if packed_bit_width == 8:
            s[1:] = source[4:].astype("b")
        else:
            delta_i = 1
            nbits = 0
            bits = 0
            byte_i = 4
            while delta_i < len(s):
                while nbits < packed_bit_width:
                    bits |= source[byte_i] << (24 - nbits)
                    nbits += 8
                    byte_i += 1
                s[delta_i] = inverse_twos_comp(
                    bits >> (32 - packed_bit_width) & 0xFFFF, packed_bit_width
                )
                delta_i += 1
                bits = (bits << packed_bit_width) & 0xFFFFFFFF
                nbits -= packed_bit_width
        current_frame += np.cumsum(s)  # expand deltas and delta-deltas
        pix_signed = current_frame[self._get_snake()]  # remove snake ordering
        return pix_signed.astype("H")  # cast unsigned

    def _get_snake(self):
        if not hasattr(self, "snake_cache"):
            width = self.x_resolution
            height = self.y_resolution
            linear = np.arange(width * height, dtype="I")
            twisted = linear + ((linear // width) & 1) * (
                width - 1 - 2 * (linear % width)
            )
            self.snake_cache = twisted.reshape(height, width)
        return self.snake_cache

    lookup_cache = {}

    def _fetch_aux(self, packed_bit_width):
        width = self.x_resolution
        height = self.y_resolution
        key = (width, height, packed_bit_width)
        if not key in self.lookup_cache:
            lookup = np.arange(0, width * height - 1) * packed_bit_width
            lookup_byte = (
                lookup // 8 + 5
            )  # 8 bits per byte, with 4+1 bytes offset from start
            lookup_bit = 16 - packed_bit_width - (lookup & 7)
            # 'I' might be faster on arm? need to profile
            lookup_bit = lookup_bit.astype("B")
            self.lookup_cache[key] = (lookup_byte - 1, lookup_byte, lookup_bit)
        return self.lookup_cache[key]


def inverse_twos_comp(v, width):
    """Convert a two's complement value of a specific bit width to a
    full width integer.

    The inverse of twos_comp() in writer.pyx.
    """
    mask = 1 << (width - 1)
    return -(v & mask) + (v & ~mask)

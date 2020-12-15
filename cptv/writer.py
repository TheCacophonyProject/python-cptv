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

import gzip
import struct
from io import BytesIO
from datetime import datetime, timedelta

import numpy as np

from .frame import Frame
from .reader import Section, Field

MAGIC = b"CPTV"
VERSION = b"\x02"
COLS = 160
ROWS = 120


class CPTVWriter:

    timestamp = None
    device_name = None
    latitude = None
    longitude = None
    altitude = None
    accuracy = None
    loc_timestamp = None
    preview_secs = None
    device_id = None
    motion_config = None
    fps = None
    model = None
    brand = None
    firmware = None
    camera_serial = None
    background_frame = None

    def __init__(self, fileobj):
        self.timestamp = datetime.now()
        self.fileobj = fileobj

    def write_header(self):
        if not self.timestamp:
            self.timestamp = datetime.now()

        mtime = self.timestamp.timestamp()
        self.s = gzip.GzipFile(fileobj=self.fileobj, mode="wb", mtime=mtime)
        self.comp = Compressor()

        self.s.write(MAGIC)
        self.s.write(VERSION)

        fw = FieldWriter()
        fw.uint8(ord(Field.COMPRESSION), 1)
        fw.uint32(ord(Field.X_RESOLUTION), COLS)
        fw.uint32(ord(Field.Y_RESOLUTION), ROWS)

        if self.device_name:
            fw.string(ord(Field.DEVICENAME), self.device_name)

        if self.device_id:
            fw.uint32(ord(Field.DEVICEID), self.device_id)

        fw.timestamp(ord(Field.TIMESTAMP), self.timestamp)

        if self.preview_secs:
            fw.uint8(ord(Field.PREVIEW_SECS), self.preview_secs)

        if self.motion_config:
            fw.string(ord(Field.MOTION_CONFIG), self.motion_config)

        if self.latitude:
            fw.float32(ord(Field.LATITUDE), self.latitude)

        if self.longitude:
            fw.float32(ord(Field.LONGITUDE), self.longitude)

        if self.altitude:
            fw.float32(ord(Field.ALTITUDE), self.altitude)

        if self.accuracy:
            fw.float32(ord(Field.ACCURACY), self.accuracy)

        if self.loc_timestamp:
            fw.timestamp(ord(Field.LOC_TIMESTAMP), self.loc_timestamp)

        if self.fps:
            fw.uint8(ord(Field.FPS), self.fps)

        if self.model:
            fw.string(ord(Field.MODEL), self.model)

        if self.brand:
            fw.string(ord(Field.BRAND), self.brand)

        if self.firmware:
            fw.string(ord(Field.FIRMWARE), self.firmware)

        if self.camera_serial:
            fw.uint32(ord(Field.CAMERA_SERIAL), self.camera_serial)

        if self.background_frame is not None:
            fw.uint8(ord(Field.BACKGROUND_FRAME), 1)

        fw.write(ord(Section.HEADER), self.s)

        if self.background_frame is not None:
            self.write_frame(self.background_frame)

    def write_frame(self, frame):
        bit_width, start_value, frame_buf = self.comp._next_frame(frame.pix)

        fw = FieldWriter()
        fw.uint32(ord(Field.TIME_ON), frame.time_on / timedelta(milliseconds=1))
        fw.uint32(
            ord(Field.LAST_FFC_TIME), frame.last_ffc_time / timedelta(milliseconds=1)
        )
        fw.uint8(ord(Field.BIT_WIDTH), bit_width)
        fw.float32(ord(Field.TEMP_C), frame.temp_c)
        fw.float32(ord(Field.LAST_FFC_TEMP_C), frame.last_ffc_temp_c)

        if frame.background_frame:
            fw.uint8(ord(Field.BACKGROUND_FRAME), 1)

        fw.uint32(ord(Field.FRAME_SIZE), len(frame_buf) + 4)
        fw.write(ord(Section.FRAME), self.s)

        self.s.write(struct.pack("<l", start_value))
        self.s.write(frame_buf)

    def close(self):
        self.s.close()


class FieldWriter:
    def __init__(self):
        self.s = BytesIO()
        self.count = 0

    def write(self, section_type, dest):
        dest.write(struct.pack("<BB", section_type, self.count))
        dest.write(self.s.getbuffer())

    def timestamp(self, code, t):
        micros = int(t.timestamp() * 1e6)
        self.uint64(code, micros)

    def uint8(self, code, val):
        self.s.write(struct.pack("<BBB", 1, code, val))
        self.count += 1

    def uint32(self, code, val):
        self.s.write(struct.pack("<BBL", 4, code, int(val)))
        self.count += 1

    def uint64(self, code, val):
        self.s.write(struct.pack("<BBQ", 8, code, val))
        self.count += 1

    def float32(self, code, fval):
        self.s.write(struct.pack("<BBf", 4, code, fval))
        self.count += 1

    def string(self, code, val):
        self.s.write(struct.pack("<BB", len(val), code))
        self.s.write(val)
        self.count += 1


class Compressor:
    def _get_twisted(self):
        if not hasattr(self, "twisted"):
            width = COLS
            height = ROWS
            linear = np.arange(width * height, dtype="I")
            self.twisted = linear + ((linear // width) & 1) * (
                width - 1 - 2 * (linear % width)
            )
        return self.twisted

    def _next_frame(self, pix):
        twisted = self._get_twisted()
        linear_pix = pix.ravel().astype("h")[twisted]

        delta = linear_pix
        if hasattr(self, "prev_linear_pix"):
            delta = linear_pix - self.prev_linear_pix
        else:
            delta = linear_pix

        self.prev_linear_pix = linear_pix

        # Now generate the adjacent "delta of deltas".
        del_delta = np.diff(delta)

        # How many bits required to store the largest delta?
        max_delta = max(abs(del_delta))
        width = 1 + int.bit_length(int(max_delta))

        # play nice with the gzip compression
        if width > 12:
            width = max(width, 16)
        elif width > 8:
            width = max(width, 12)
        else:
            width = 8

        # Pack the deltas according to the bit width determined
        pack_data = self.pack_bits(width, del_delta).astype("B")

        return width, delta[0], pack_data

    def pack_bits(self, packed_bit_width, vals):
        if packed_bit_width == 8:
            return vals

        if packed_bit_width == 12:
            mask = (1 << packed_bit_width) - 1
            twos_complement = vals & mask

            stacked = twos_complement << 4
            stacked[:-1] += twos_complement[1:] >> 8

            result_len = (len(vals) * 3 + 1) // 2
            result = np.empty(result_len, "B")

            result[np.arange(0, result_len, 3)] = vals[np.arange(0, len(vals), 2)] >> 4
            result[np.arange(1, result_len, 3)] = stacked[np.arange(0, len(vals), 2)]
            result[np.arange(2, result_len, 3)] = vals[np.arange(1, len(vals), 2)]
            return result

        return self.pack_bits_fallback(packed_bit_width, vals)

    def pack_bits_fallback(self, packed_bit_width, vals):
        # Hopefully not used
        result_len = (len(vals) * packed_bit_width + 7) // 8

        result = np.empty(result_len, "I")
        index = 0
        bits = 0  # scratch buffer
        num_bits = 0  # number of bits in use in scratch
        mask = (1 << packed_bit_width) - 1

        for val in vals:
            bits |= (val & mask) << (32 - packed_bit_width - num_bits)
            num_bits += packed_bit_width
            while num_bits >= 8:
                result[index] = bits
                index = index + 1
                bits <<= 8
                num_bits -= 8

        if num_bits > 0:
            result[index] = bits

        return result >> 24

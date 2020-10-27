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

from io import BytesIO
from datetime import datetime, timedelta, timezone

import numpy as np
from pytest import approx


from cptv import CPTVWriter, CPTVReader
from cptv.frame import Frame


def test_round_trip_header_defaults():
    buf = BytesIO()

    w = CPTVWriter(buf)
    w.write_header()
    w.close()

    buf.seek(0, 0)

    r = CPTVReader(buf)
    assert r.version == 2
    assert r.x_resolution == 160
    assert r.y_resolution == 120
    assert not r.device_name
    assert not r.device_id
    assert (datetime.now(tz=timezone.utc) - r.timestamp) < timedelta(minutes=1)
    assert r.latitude == 0
    assert r.longitude == 0

    assert r.accuracy == 0
    assert r.altitude == 0
    assert r.fps == 0
    assert r.model is None
    assert r.brand is None
    assert r.firmware is None
    assert r.camera_serial == 0


def test_round_trip_header():
    buf = BytesIO()

    w = CPTVWriter(buf)
    w.timestamp = datetime(2018, 7, 6, 5, 4, 3, tzinfo=timezone.utc)
    w.device_name = b"hello"
    w.device_id = 42
    w.latitude = 142.3
    w.longitude = -39.2
    w.loc_timestamp = datetime(2018, 9, 6, 5, 4, 3, tzinfo=timezone.utc)

    w.preview_secs = 3
    w.motion_config = b"blob"
    w.accuracy = 20
    w.altitude = 200
    w.fps = 30
    w.model = b"ultra"
    w.brand = b"laser"
    w.firmware = b"killer"
    w.camera_serial = 221

    w.write_header()
    for i in range(10):
        frame = random_frame(60, 30)
        w.write_frame(frame)
    w.close()

    buf.seek(0, 0)

    r = CPTVReader(buf)
    assert r.version == 2
    assert r.x_resolution == 160
    assert r.y_resolution == 120
    assert r.timestamp == w.timestamp
    assert r.device_name == w.device_name
    assert r.device_id == w.device_id
    assert r.latitude == approx(w.latitude, 0.000001)
    assert r.longitude == approx(w.longitude, 0.000001)
    assert r.loc_timestamp == w.loc_timestamp
    assert r.preview_secs == w.preview_secs
    assert r.motion_config == w.motion_config

    assert r.accuracy == w.accuracy
    assert r.altitude == w.altitude
    assert r.fps == w.fps
    assert r.model == w.model
    assert r.brand == w.brand
    assert r.firmware == w.firmware
    assert r.camera_serial == w.camera_serial


def test_one_frame():
    check_frames([random_frame(60, 30)])


def test_random_frames():
    check_frames([random_frame(60, 30), random_frame(61, 31), random_frame(62, 32)])


def test_minimal_change():
    frame0 = random_frame(0, 0)

    # Change one pixel
    pix1 = frame0.pix.copy()
    pix1[0, 0] += 1
    frame1 = new_frame(pix1)

    check_frames([frame0, frame1])


def test_step_change():
    frame0 = random_frame(0, 0)

    pix1 = frame0.pix.copy()
    pix1 += 1
    frame1 = new_frame(pix1)

    check_frames([frame0, frame1])


def test_large_value():
    frame0 = random_frame(0, 0)

    pix1 = frame0.pix.copy()
    pix1[0] += 32767
    frame1 = new_frame(pix1)

    check_frames([frame0, frame1])


def check_frames(frames):
    buf = BytesIO()
    w = CPTVWriter(buf)
    w.write_header()
    for frame in frames:
        w.write_frame(frame)
    w.close()

    buf.seek(0, 0)

    r = CPTVReader(buf)
    count = 0
    for in_frame, out_frame in zip(frames, r):
        assert in_frame == out_frame
        count += 1

    assert count == len(frames)


def new_frame(pix):
    return Frame(pix, timedelta(seconds=0), timedelta(seconds=0), 0.0, 0.0)


def random_frame(time_on, last_ffc_time, min_value=None, max_value=None):
    if min_value is None:
        min_value = 3000
    if max_value is None:
        max_value = 6000
    return Frame(
        np.random.randint(min_value, max_value, (120, 160), "uint16"),
        timedelta(seconds=time_on),
        timedelta(seconds=last_ffc_time),
        np.random.randint(2800, 3000),
        np.random.randint(2800, 3000),
    )

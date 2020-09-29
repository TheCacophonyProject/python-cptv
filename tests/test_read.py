from datetime import datetime, timezone
from pathlib import Path

from pytest import approx

from cptv import CPTVReader


data_dir = Path(__file__).parent / "data"


def test_read_v1():
    filename = str(data_dir / "v1.cptv")
    with open(filename, "rb") as f:
        r = CPTVReader(f)
        assert r.version == 1
        assert r.device_name == b"livingsprings03"
        assert r.device_id == 0
        assert r.timestamp == datetime(2018, 9, 6, 9, 21, 25, 774768, timezone.utc)
        assert r.x_resolution == 160
        assert r.y_resolution == 120
        assert r.preview_secs == 0
        assert r.motion_config is None
        assert r.latitude == 0
        assert r.longitude == 0
        assert r.altitude == 0
        assert r.fps == 0
        assert r.model is None
        assert r.brand is None
        assert r.firmware is None
        assert r.camera_serial == 0

        count = 0
        for frame in r:
            count += 1
            assert frame.last_ffc_temp_c == 0
            assert frame.temp_c == 0
            assert frame.time_on is None
            assert frame.last_ffc_time is None
            assert frame.pix.min() > 2500
            assert frame.pix.max() < 3200
        assert count == 100


def test_read_v2():
    filename = str(data_dir / "v2.cptv")
    with open(filename, "rb") as f:
        r = CPTVReader(f)
        assert r.version == 2
        assert r.device_id == 44
        assert r.device_name == b"nz99"
        assert r.timestamp == datetime(2018, 9, 6, 9, 21, 25, 774768, timezone.utc)
        assert r.x_resolution == 160
        assert r.y_resolution == 120
        assert r.preview_secs == 1
        assert r.motion_config == b"motion"
        assert r.latitude == 0
        assert r.longitude == 0
        assert r.loc_timestamp == 0

        assert r.altitude == 0
        assert r.fps == 0
        assert r.model is None
        assert r.brand is None
        assert r.firmware is None
        assert r.camera_serial == 0
        count = 0
        for frame in r:
            count += 1
            assert frame.time_on is not None
            assert frame.last_ffc_time is not None
            assert frame.pix.min() > 2500
            assert frame.pix.max() < 3200
        assert count == 100


#
# def test_read_v2():
#     filename = str(data_dir / "v3.cptv")
#     with open(filename, "rb") as f:
#         r = CPTVReader(f)
#         assert r.version == 3
#         assert r.device_id == 42
#         assert r.device_name == b"hello"
#         assert r.timestamp == datetime(2018, 7, 6, 5, 4, 3, tzinfo=timezone.utc)
#         assert r.x_resolution == 160
#         assert r.y_resolution == 120
#         assert r.preview_secs == 3
#         assert r.motion_config == b"blob"
#         assert int(r.latitude) == 142
#         assert int(r.longitude) == -39
#         assert r.loc_timestamp == datetime(2018, 9, 6, 5, 4, 3, tzinfo=timezone.utc)
#         assert r.accuracy == 20
#         assert r.altitude == 200
#         assert r.fps == 30
#         assert r.model == b"ultra"
#         assert r.brand == b"laser"
#         assert r.firmware == b"killer"
#         assert r.camera_serial == 221
#         count = 0
#         for frame in r:
#             count += 1
#             assert frame.time_on is not None
#             assert frame.last_ffc_time is not None
#             assert frame.last_ffc_temp_c != 0
#             assert frame.temp_c != 0
#         assert count == 10


def test_lat_lon():
    filename = str(data_dir / "v2-latlon.cptv")
    with open(filename, "rb") as f:
        r = CPTVReader(f)
        assert r.version == 2
        assert r.latitude == approx(-36.943634)
        assert r.longitude == approx(174.661544)

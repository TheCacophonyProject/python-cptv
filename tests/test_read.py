from datetime import datetime, timezone
from pathlib import Path

from cptv import CPTVReader


data_dir = Path(__file__).parent / "data"


def test_read_v1():
    filename = str(data_dir / "v1.cptv")
    with open(filename, "rb") as f:
        r = CPTVReader(f)
        assert r.version == 1
        assert r.device_name == b"livingsprings03"
        assert r.timestamp == datetime(2018, 9, 6, 9, 21, 25, 774768, timezone.utc)
        assert r.x_resolution == 160
        assert r.y_resolution == 120
        assert r.preview_secs == 0
        assert r.motion_config is None

        count = 0
        for frame in r:
            count += 1
            assert frame.time_on is None
            assert frame.last_ffc_time is None
        assert count == 100


def test_read_v2():
    filename = str(data_dir / "v2.cptv")
    with open(filename, "rb") as f:
        r = CPTVReader(f)
        assert r.version == 2
        assert r.device_name == b"nz99"
        assert r.timestamp == datetime(2018, 9, 6, 9, 21, 25, 774768, timezone.utc)
        assert r.x_resolution == 160
        assert r.y_resolution == 120
        assert r.preview_secs == 1
        assert r.motion_config == b"motion"

        count = 0
        for frame in r:
            count += 1
            assert frame.time_on is not None
            assert frame.last_ffc_time is not None
        assert count == 100

from io import StringIO
from datetime import datetime

from cptv import CPTVWriter, CPTVReader
from cptv.frame import Frame


def test_round_trip():
    now = datetime.now()
    buf = StringIO()

    w = CPTVWriter(buf)
    # w.timestamp = now
    # w.device_name = b"hello"
    # w.preview_secs = 3
    # w.latitude = 142.2
    # w.longitude = -39.2

    w.write_header()
    w.close()

    buf.seek(0, 0)

    r = CPTVReader(buf)
    assert r.version == 2
    assert r.x_resolution == 160
    assert r.y_resolution == 120

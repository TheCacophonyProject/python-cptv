import io
import pytest
from cptv.bitstream import BitStream


def test_single_bytes():
    b = BitStream(io.BytesIO(b'\xff\xee\xdd'))
    assert b.bytes(1) == b'\xff'
    assert b.bytes(1) == b'\xee'
    assert b.bytes(1) == b'\xdd'


def test_multi_bytes():
    b = BitStream(io.BytesIO(b'\xff\xee\xdd'))
    assert b.bytes(3) == b'\xff\xee\xdd'


def test_not_enough_bytes():
    b = BitStream(io.BytesIO(b'\xff'))
    with pytest.raises(EOFError, match="short read. wanted 2, got 1"):
        b.bytes(2)


def test_uint8():
    b = BitStream(io.BytesIO(b'\xff\x01\x00'))
    assert b.uint8() == 255
    assert b.uint8() == 1
    assert b.uint8() == 0


def test_uint32():
    b = BitStream(io.BytesIO(b'\xff\xee\xdd\xaa'))
    assert b.uint32() == 0xaaddeeff


def test_uint64():
    b = BitStream(io.BytesIO(b'\xff\xee\xdd\xcc\xbb\xaa\x00\x11'))
    assert b.uint64() == 0x1100aabbccddeeff


def test_iter_int():
    i = BitStream(io.BytesIO(b'\xf0\x13')).iter_int(2, 4)
    assert next(i) == -1
    assert next(i) == 0x0
    assert next(i) == 0x1
    assert next(i) == 0x3

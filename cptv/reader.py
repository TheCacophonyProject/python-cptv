import datetime
import gzip
import shutil
import tempfile

from bitstring import ConstBitStream, ReadError
import numpy as np


class Section:
    HEADER = b'H'
    FRAME = b'F'


class Field:
    TIMESTAMP = b'T'
    X_RESOLUTION = b'X'
    Y_RESOLUTION = b'Y'
    COMPRESSION = b'C'
    BIT_WIDTH = b'w'
    FRAME_SIZE = b'f'


UINT_FIELDS = {
    Field.X_RESOLUTION,
    Field.Y_RESOLUTION,
    Field.COMPRESSION,
    Field.BIT_WIDTH,
    Field.FRAME_SIZE,
}

epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)


class CPTVReader:
    """
    CPTVReader is a parser and decompressor for Cacophony Project
    Thermal Video files.

    Usage:

        reader = CPTVReader(file_object)
        print(reader.timestamp)
        print(reader.x_resolution)
        print(reader.y_resolution)

        for frame in reader:
            print(frame)  # frame is a 2D numpy array

    """

    def __init__(self, fileobj):
        # Create a temporary file with the decompressed output because
        # bitstring wants the mmap the file which doesn't work with a
        # GzipFile. On POSIX at least, the temporary file gets
        # unlinked from the filesystem but the ConstBitStream can
        # still work with the open file handle.
        with tempfile.TemporaryFile() as tmpF:
            with gzip.GzipFile(fileobj=fileobj, mode="rb") as gz_file:
                shutil.copyfileobj(gz_file, tmpF)
            self.s = ConstBitStream(tmpF)

        # check magic and version
        if self.s.read("bytes:4") != b"CPTV":
            raise IOError("magic not found")

        if self.s.read("uint:8") != 1:
            raise IOError("unsupported version")

        section_type, fields = self._read_section()
        if section_type != Section.HEADER:
            raise IOError("header not found")

        self.compression = fields[Field.COMPRESSION]
        if self.compression != 1:
            raise ValueError("unsupported compression type: {}".format(self.compression))

        self.timestamp = fields[Field.TIMESTAMP]
        self.x_resolution = fields[Field.X_RESOLUTION]
        self.y_resolution = fields[Field.Y_RESOLUTION]
        self.frame_dim = (self.y_resolution, self.x_resolution)

    def __iter__(self):
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
            except ReadError:
                return
            if section_type != Section.FRAME:
                raise IOError("unexpected section: {}".format(section_type))

            frame_size = fields[Field.FRAME_SIZE]
            bit_width = fields[Field.BIT_WIDTH]
            read_fmt = 'int:'+str(bit_width)

            # For some reason, it's signficantly faster to read the
            # full frame into memory and then pull it apart from
            # there.
            s = self.s.read('bits:'+str(8*frame_size))
            s_read_inner = s.read

            # Assemble the delta frame
            v = s_read_inner('intle:32')  # read starting value...

            # ... then apply deltas
            delta_frame[0][0] = v
            for y, x in walk_coords:
                v += s_read_inner(read_fmt)
                delta_frame[y][x] = v

            # Calculate the frame by applying the delta frame to the
            # previously decompressed frame.
            frame = (prev_frame + delta_frame).astype('uint16')
            yield frame
            prev_frame = frame

    def _read_section(self):
        section_type = self.s.read('bytes:1')
        field_count = self.s.read('uint:8')
        fields = {}
        for _ in range(field_count):
            ftype, value = self._read_field()
            fields[ftype] = value
        return section_type, fields

    def _read_field(self):
        data_len = self.s.read('uint:8')
        ftype = self.s.read('bytes:1')

        if ftype in UINT_FIELDS:
            val = self.s.read('uintle:' + str(8 * data_len))
        elif ftype == Field.TIMESTAMP:
            micros = self.s.read('uintle:' + str(8 * data_len))
            val = epoch + datetime.timedelta(microseconds=micros)
        else:
            # Unknown field, just slurp up the bytes
            val = self.s.read('bytes:' + str(data_len))

        return ftype, val

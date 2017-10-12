from bitstring import ConstBitStream, ReadError
import datetime
import gzip
import numpy as np
import shutil
import tempfile

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

        self.prev_frame = np.zeros(self.frame_dim, dtype="uint16")

    def __iter__(self):
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

            # Assemble the delta frame
            v = self.s.read('intle:32')  # read starting value...

            # ... then apply deltas
            delta_frame = np.zeros(self.frame_dim, dtype="int32")
            delta_frame[0][0] = v
            num_deltas = (self.x_resolution * self.y_resolution) - 1

            # offset by 1 b/c we already have initial value
            for i in range(1, num_deltas+1):
                y = i // self.x_resolution
                x = i % self.x_resolution
                # Deltas are "snaked" so work backwards through every
                # second row.
                if y % 2 == 1:
                    x = self.x_resolution - x - 1
                v += self.s.read(read_fmt)
                delta_frame[y][x] = v

            # Calculate the frame by applying the delta frame to the
            # previously decompressed frame.
            frame = (self.prev_frame + delta_frame).astype('uint16')

            self.prev_frame = frame
            self.s.bytealign()
            yield frame

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

        if ftype == Field.TIMESTAMP:
            micros = self.s.read('uintle:' + str(8 * data_len))
            val = epoch + datetime.timedelta(microseconds=micros)
        elif ftype in UINT_FIELDS:
            val = self.s.read('uintle:' + str(8 * data_len))
        else:
            # Unknown field, just slurp up the bytes
            val = self.s.read('bytes:' + str(data_len))

        return ftype, val

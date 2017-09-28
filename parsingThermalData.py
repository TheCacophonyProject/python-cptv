# sudo pip install Pillow

import binascii
import gzip
import sys
import struct
import numpy as np
import cv2
from bitstring import ConstBitStream
from PIL import Image
from os.path import join

FOLDER_NAME = "images2"
FILE_NAME = "10-compressed.cptv"

def process_frame_to_rgb(frame):
    a = np.zeros((120, 160))
    a = cv2.normalize(frame, a, 0, 65535, cv2.NORM_MINMAX)
    maximum = np.amax(a)
    minimum = np.amin(a)
    m1 = 0.25*65535
    m2 = 0.50*65535
    m3 = 0.75*65535
    b1 = np.where(a <=m1, 1, 0)
    b2 = np.where(np.bitwise_and(m1 < a, a <=m2), 1, 0)
    b3 = np.where(np.bitwise_and(m2 < a, a <=m3), 1, 0)
    b4 = np.where(m3 < a, 1, 0)
    rgb = np.zeros((120, 160, 3), 'uint8')
    rgb[..., 0] = ((a-0.5*65535)*255*4/65535.0*b3 + b4*255)
    rgb[..., 1] = (b2*255 + b3*255 + b1*255*a*4/65535.0 + b4*255*((65535.0-a)*4/65535.0))
    rgb[..., 2] = (b1*255 + b2*255*((0.5*65535.0-a)*4)/65535.0 )
    return rgb

def save_rgb_as_image(rgb, n, folder):
    im = Image.fromarray(rgb, "RGB")
    imName = str(n).zfill(6) + '.png'
    im.save(join(folder, imName))

def get_frame_headers(f):
    number_of_frame_fields = struct.unpack('B', f.read(1))[0]
    for i in range(number_of_frame_fields):
        dataLen = struct.unpack('B', f.read(1))[0]
        field_type = f.read(1)
        if field_type == "t":
            offset = struct.unpack('I', f.read(dataLen))[0]
        elif field_type == "w":
            bit_width = struct.unpack('B', f.read(dataLen))[0]
        elif field_type == "f":
            frame_size = struct.unpack('I', f.read(dataLen))[0]
    return offset, bit_width, frame_size

def compression_0(f):
    ## Start of frame
    n = 0
    while f.read(1) == "F":
        n += 1
        offset, bit_width, frame_size = get_frame_headers(f)

        ## Read frame data
        stream = ConstBitStream(bytes=f.read(frame_size))

        #numpy_data = np.array(stream.readlist(['uintle:'+str(bit_width)]*y_res*x_res))
        numpy_data = np.zeros((y_res, x_res))
        for y in range(y_res):
            for x in range(x_res):
                numpy_data[y][x] = stream.read('uintle:'+str(bit_width))

        numpy_data = np.resize(numpy_data, (y_res, x_res)).astype(np.uint16)
        print(n)
        rgb = process_frame_to_rgb(numpy_data)
        save_rgb_as_image(rgb, n, FOLDER_NAME)

def compression_1(f):
    # TODO: reuse frame arrays instead of allocating new ones all
    # the time.
    prevFrame = np.zeros((y_res, x_res), dtype="uint16")
    deltaFrame = np.zeros((y_res, x_res), dtype="int32")
    n = 0
    while f.read(1) == "F":
        print "=== FRAME %d ===" % n
        n += 1
        offset, bit_width, frame_size = get_frame_headers(f)
        print "bit width: %d" % bit_width

        stream = ConstBitStream(bytes=f.read(frame_size))
        val = stream.read('intle:32')
        deltaFrame[0][0] = val
        num_deltas = (x_res * y_res) - 1

        # offset by 1 b/c we already have initial value
        for i in range(1, num_deltas+1):
            y = i // x_res
            x = i % x_res
            # Deltas are "snaked" so work backwards through every
            # second row.
            if y % 2 == 1:
                x = x_res - x - 1

            val += stream.read('int:'+str(bit_width))
            deltaFrame[y][x] = val

        # Calculate the frame by applying the delta frame to the
        # previously decompressed frame.
        frame = (prevFrame + deltaFrame).astype('uint16')

        print frame
        prevFrame = frame


with gzip.open(FILE_NAME, "rb") as f:
    if (f.read(4) != "CPTV"):
        print("No CPTV found.")
        sys.exit()
    versioncode = f.read(1)
    print("Version code: " + binascii.hexlify(versioncode))

    if (f.read(1) != "H"):
        print("No header field found.")
        sys.exit()

    ## Process header
    number_of_header_fields = struct.unpack('B', f.read(1))[0]
    print("Number of header fields: " + str(number_of_header_fields))

    for i in range(number_of_header_fields):
        dataLen = struct.unpack('B', f.read(1))[0]
        field_type = f.read(1)
        if field_type == "T":
            timestamp = struct.unpack('Q', f.read(dataLen))[0]
        elif field_type == "X":
            x_res = struct.unpack('I', f.read(dataLen))[0]
        elif field_type == "Y":
            y_res = struct.unpack('I', f.read(dataLen))[0]
        elif field_type == "C":
            compression = struct.unpack('B', f.read(dataLen))[0]

    print("Timestamp: " + str(timestamp))
    print("X res:" + str(x_res))
    print("Y res:" + str(y_res))
    print("Compression:" + str(compression))

    if compression == 0:
        compression_0(f)
    elif compression == 1:
        compression_1(f)

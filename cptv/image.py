# Copyright 2017 The Cacophony Project
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

from PIL import Image
import cv2
import numpy as np


def save_frame(frame, filename):
    rgb = process_frame_to_rgb(frame)
    rgb_to_png(rgb, filename)


def process_frame_to_rgb(frame):
    a = np.zeros((120, 160))
    a = cv2.normalize(frame, a, 0, 65535, cv2.NORM_MINMAX)
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


def rgb_to_png(rgb, filename):
    im = Image.fromarray(rgb, "RGB")
    im.save(filename)

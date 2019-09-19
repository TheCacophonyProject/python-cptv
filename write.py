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

# This file shows an example of how to generate a CPTV file.

import sys
from datetime import datetime
from typing import Iterable

from cptv import CPTVWriter, Frame


def write_cptv(frames: Iterable[Frame], filename: str):
    with open(filename, "wb") as f:
        w = CPTVWriter(f)
        w.timestamp = datetime.now()
        w.device_name = b"foo42"
        w.latitude = 142.2
        w.longitude = -39.2
        w.preview_secs = 3
        w.motion_config = b"stuff"
        w.write_header()

        for frame in frames:
            w.write_frame(frame)

        w.close()

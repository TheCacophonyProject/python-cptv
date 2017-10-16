#!/usr/bin/python3

import sys
import pytz

from cptv import CPTVReader

local_tz = pytz.timezone('Pacific/Auckland')

reader = CPTVReader(open(sys.argv[1], "rb"))
print(reader.timestamp.astimezone(local_tz))

for i, (frame, offset) in enumerate(reader):
    print(i, offset, frame.min(), frame.max())

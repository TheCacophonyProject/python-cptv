#!/usr/bin/python3

import sys
from cptv import CPTVReader

reader = CPTVReader(open(sys.argv[1], "rb"))
print(reader.timestamp)

count = 0
for frame in reader:
    count += 1
print(count)

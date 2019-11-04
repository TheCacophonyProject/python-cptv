import sys
from cptv import CPTVReader


filename = sys.argv[1]

with open(filename, "rb") as f:
    reader = CPTVReader(f)
    print("version:", reader.version)
    print("device name:", reader.device_name)
    print("device id:", reader.device_id)
    print("time:", reader.timestamp)
    print("dims:", reader.x_resolution, reader.y_resolution)
    print("location:", reader.latitude, reader.longitude)
    print("preview secs:", reader.preview_secs)
    print("motion config:", reader.motion_config)

    for frame in reader:
        print(
            "t:",
            frame.time_on,
            "ffc:",
            frame.last_ffc_time,
            "min:",
            frame.pix.min(),
            "max:",
            frame.pix.max(),
        )

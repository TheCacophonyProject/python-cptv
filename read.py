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
    print("location timestamp:", reader.loc_timestamp)

    print("preview secs:", reader.preview_secs)
    print("motion config:", reader.loc_timestamp)

    print("altitude:", reader.altitude)
    print("fps:", reader.fps)
    print("model:", reader.model)
    print("brand:", reader.brand)
    print("firmware:", reader.firmware)
    print("camera_serial:", reader.camera_serial)
    t0 = None

    for frame in reader:
        if t0 is None:
            t0 = frame.time_on
        print(
            f"{frame.time_on - t0} ({frame.time_on}) - ffc: {frame.time_on - frame.last_ffc_time}, min: {frame.pix.min()}, max: {frame.pix.max()}, temp_c: {frame.temp_c}, last_ffc_temp_c: {frame.last_ffc_temp_c}"
        )

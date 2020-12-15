import numpy as np


class Frame:
    """
    Frame stores the thermal pixels for single CPTV video frame and
    some associated metadata.
    """

    pix = None
    time_on = None
    last_ffc_time = None

    def __init__(
        self,
        pix,
        time_on,
        last_ffc_time,
        temp_c,
        last_ffc_temp_c,
        background_frame=False,
    ):
        self.pix = pix
        self.time_on = time_on
        self.last_ffc_time = last_ffc_time
        self.temp_c = temp_c
        self.last_ffc_temp_c = last_ffc_temp_c
        self.background_frame = background_frame

    def __repr__(self):
        return "<Frame t={} ffc_t={} pix={!r} temp={} last_ffc_temp={} background_frame={}".format(
            self.time_on,
            self.last_ffc_time,
            self.pix,
            self.temp_c,
            self.last_ffc_temp_c,
            self.background_frame,
        )

    def __eq__(self, other):
        return (
            self.temp_c == other.temp_c
            and self.last_ffc_temp_c == other.last_ffc_temp_c
            and self.time_on == other.time_on
            and self.last_ffc_time == other.last_ffc_time
            and np.array_equal(self.pix, other.pix)
        )

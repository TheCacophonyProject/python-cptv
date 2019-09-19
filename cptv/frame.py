import numpy as np


class Frame:
    """
    Frame stores the thermal pixels for single CPTV video frame and
    some associated metadata.
    """

    __slots__ = "pix", "time_on", "last_ffc_time"

    def __init__(self, pix, time_on, last_ffc_time):
        self.pix = pix
        self.time_on = time_on
        self.last_ffc_time = last_ffc_time

    def __repr__(self):
        return "<Frame t={} ffc_t={} pix={!r}".format(
            self.time_on, self.last_ffc_time, self.pix
        )

    def __eq__(self, other):
        return (
            self.time_on == other.time_on
            and self.last_ffc_time == other.last_ffc_time
            and np.array_equal(self.pix, other.pix)
        )

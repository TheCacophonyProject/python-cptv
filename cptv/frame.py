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

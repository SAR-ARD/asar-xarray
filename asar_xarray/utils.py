import numpy as np
from datetime import datetime, timedelta

def get_mjd(mjd_str: str) -> np.datetime64:
    """
    Convert Modified Julian Date string to numpy datetime64.

    MJD strings from ASAR data are typically in the form "days, seconds, microseconds"
    where days are counted from 1950-01-01.

    :param mjd_str: String containing MJD in format "days, seconds, microseconds"
    :return: numpy datetime64 object
    """
    if not mjd_str:
        return None

    # Clean and split the string
    parts = mjd_str.replace(',', ' ').split()

    # Convert parts to integers, with defaults if missing
    days = int(parts[0]) if len(parts) > 0 else 0
    seconds = int(parts[1]) if len(parts) > 1 else 0
    microseconds = int(parts[2]) if len(parts) > 2 else 0

    # MJD reference date is 1950-01-01
    mjd_epoch = datetime(1950, 1, 1)

    # Calculate the datetime
    dt = mjd_epoch + timedelta(days=days,
                              seconds=seconds,
                              microseconds=microseconds)

    # Convert to numpy datetime64
    return np.datetime64(dt, 'ns')

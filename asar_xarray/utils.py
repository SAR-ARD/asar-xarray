import numpy as np
from datetime import datetime, timedelta

# TODO: update documentation
def get_envisat_time(mjd_str: str) -> np.datetime64:
    """

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

    # MJD reference date is 2000-01-01
    mjd_epoch = datetime(2000, 1, 1)

    # Calculate the datetime
    dt = mjd_epoch + timedelta(days=days,
                              seconds=seconds,
                              microseconds=microseconds)

    # Convert to numpy datetime64
    return np.datetime64(dt, 'ns')

def get_mjd_time(mjd_str: str) -> np.datetime64:
    """

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

    # MJD reference date is 1858-11-17
    mjd_epoch = datetime(1858, 11, 17)

    # Calculate the datetime
    dt = mjd_epoch + timedelta(days=days,
                              seconds=seconds,
                              microseconds=microseconds)

    # Convert to numpy datetime64
    return np.datetime64(dt, 'ns')
import re

import numpy as np
from datetime import datetime, timedelta

from numpy import datetime64


def get_envisat_time(time_str: str) -> datetime64 | None:
    """
    Converts time string to envisat epoch time in numpy datetime64 format.

    :param time_str: String containing MJD in format "days, seconds, microseconds"
    :return: numpy datetime64 object
    """
    if not time_str:
        return None

    # Clean and split the string
    parts = time_str.replace(',', ' ').split()

    # Convert parts to integers, with defaults if missing
    days = int(parts[0]) if len(parts) > 0 else 0
    seconds = int(parts[1]) if len(parts) > 1 else 0
    microseconds = int(parts[2]) if len(parts) > 2 else 0

    # MJD reference date is 2000-01-01
    epoch = datetime(2000, 1, 1)

    # Calculate the datetime
    dt = epoch + timedelta(days=days,
                           seconds=seconds,
                           microseconds=microseconds)

    # Convert to numpy datetime64
    return np.datetime64(dt, 'ns')


def get_mjd_time(mjd_str: str) -> datetime64 | None:
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


def try_parse_datetime(value: str) -> np.datetime64 | None:
    datetime_pattern = re.compile(r'\d{2}-[A-Z]{3}-\d{4}\s+\d{2}:\d{2}:\d{2}')
    if datetime_pattern.match(value):
        try:
            dt = datetime.strptime(value, '%d-%b-%Y %H:%M:%S.%f')
            return np.datetime64(dt, 'ns')
        except ValueError:
            return None
    return None


def try_parse_latlong(value: str) -> float | None:
    latlong_pattern = re.compile(r'[+-]\d{10}$')
    if latlong_pattern.match(value):
        return float(value) / 1e7
    return None


def try_parse_int(value: str) -> int | None:
    numeric = value.replace('+', '-').replace('-', '')
    if numeric.isdigit():
        return int(value.replace('+', ''))
    return None


def try_parse_float(value: str) -> float | None:
    if 'E' in value or '.' in value:
        try:
            return float(value.replace('+', ''))
        except ValueError:
            return None
    return None


def try_parse_float_list(value: str) -> float | list[float] | None:
    parts = value.strip().split()
    if all(re.fullmatch(r'[+-]?\d*\.?\d+(e[+-]?\d+)?', p, re.IGNORECASE) for p in parts):
        try:
            floats = [float(p.replace('+', '')) for p in parts]
            return floats[0] if len(floats) == 1 else floats
        except ValueError:
            return None
    return None

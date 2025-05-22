"""General dataset processing utils."""

import re

import numpy as np
from datetime import datetime, timedelta

from numpy import datetime64


def get_envisat_time(time_str: str) -> datetime64 | None:
    """
    Convert time string to envisat epoch time in numpy datetime64 format.

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
    Convert mjd time to numpy.datetime64 format.

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
    """
    Attempt to parse a string into a numpy.datetime64 object.

    This function checks if the input string matches a specific datetime format
    (e.g., "DD-MMM-YYYY HH:MM:SS") and converts it into a numpy.datetime64 object
    if valid. If the string does not match the format or cannot be parsed, it returns None.

    :param value: The string to parse, expected in the format "DD-MMM-YYYY HH:MM:SS".
    :return: A numpy.datetime64 object if parsing is successful, otherwise None.
    """
    datetime_pattern = re.compile(r'\d{2}-[A-Z]{3}-\d{4}\s+\d{2}:\d{2}:\d{2}')
    if datetime_pattern.match(value):
        try:
            dt = datetime.strptime(value, '%d-%b-%Y %H:%M:%S.%f')
            return np.datetime64(dt, 'ns')
        except ValueError:
            return None
    return None


def try_parse_latlong(value: str) -> float | None:
    """
    Attempt to parse a latitude/longitude value from a string.

    This function checks if the input string matches the expected format for latitude
    or longitude values (a signed 10-digit integer). If the format is valid, it converts
    the value to a float by dividing it by 1e7. If the format is invalid, it returns None.

    :param value: The string to parse, expected to be a signed 10-digit integer.
    :return: A float representing the latitude/longitude if parsing is successful, otherwise None.
    """
    latlong_pattern = re.compile(r'[+-]\d{10}$')
    if latlong_pattern.match(value):
        return float(value) / 1e7
    return None


def try_parse_int(value: str) -> int | None:
    """
    Attempt to parse an integer value from a string.

    This function checks if the input string represents a valid integer.
    It removes any '+' or '-' signs for validation purposes and then
    converts the string to an integer if valid. If the string is not a valid
    integer, it returns None.

    :param value: The string to parse, expected to represent an integer.
    :return: An integer if parsing is successful, otherwise None.
    """
    numeric = value.replace('+', '-').replace('-', '')
    if numeric.isdigit():
        return int(value.replace('+', ''))
    return None


def try_parse_float(value: str) -> float | None:
    """
    Attempt to parse a floating-point number from a string.

    This function checks if the input string contains a valid floating-point number,
    indicated by the presence of 'E' (scientific notation) or a decimal point ('.').
    If valid, it converts the string to a float. If the string is not a valid float,
    it returns None.

    :param value: The string to parse, expected to represent a floating-point number.
    :return: A float if parsing is successful, otherwise None.
    """
    if 'E' in value or '.' in value:
        try:
            return float(value.replace('+', ''))
        except ValueError:
            return None
    return None


def try_parse_float_list(value: str) -> float | list[float] | None:
    """
    Attempt to parse a string into a float or a list of floats.

    This function splits the input string into parts and checks if each part matches
    the format of a valid floating-point number (including scientific notation).
    If all parts are valid, it converts them to floats. If there is only one float,
    it returns that float. If there are multiple floats, it returns a list of floats.
    If the input string is invalid, it returns None.

    :param value: The string to parse, expected to contain one or more floating-point numbers
                  separated by whitespace.
    :return: A single float if the input contains one valid number, a list of floats if
             multiple valid numbers are present, or None if parsing fails.
    """
    parts = value.strip().split()
    if all(re.fullmatch(r'^[+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?$', p, re.IGNORECASE) for p in parts):
        try:
            floats = [float(p.replace('+', '')) for p in parts]
            return floats[0] if len(floats) == 1 else floats
        except ValueError:
            return None
    return None

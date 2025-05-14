from datetime import datetime
import re
from typing import Any

import numpy as np
from osgeo import gdal

from asar_xarray import utils


def process_general_metadata(dataset: gdal.Dataset, attributes: dict[str, Any]) -> None:
    metadata = dataset.GetMetadata(domain='')
    attributes.update(process_mph_metadata(metadata))
    attributes.update(process_sph_metadata(metadata))
    attributes.update(process_ds_metadata(metadata))


def process_mph_metadata(metadata: dict[str, str]) -> dict[str, Any]:
    """
    Process MPH metadata by removing 'MPH_' prefix and converting values to appropriate types.
    Uses numpy.datetime64 for datetime values.

    :param metadata: Dictionary with MPH metadata
    :return: Processed metadata dictionary
    """
    processed: dict[str, Any] = {}

    for key, value in metadata.items():
        if not key.startswith('MPH_'):
            continue

        # Remove MPH_ prefix
        new_key = key[4:].lower()

        # Strip any whitespace from value
        value = value.strip()

        # Try parsing datetime first
        try:
            if re.match(r'\d{2}-[A-Z]{3}-\d{4}\s+\d{2}:\d{2}:\d{2}', value):
                # Convert datetime string to numpy.datetime64
                dt = datetime.strptime(value, '%d-%b-%Y %H:%M:%S.%f')
                processed[new_key] = np.datetime64(dt, 'ns')
                continue
        except ValueError:
            pass

        # Try parsing as float if contains decimal point or scientific notation
        if '.' in value or 'e' in value.lower():
            try:
                processed[new_key] = float(value.replace('+', ''))
                continue
            except ValueError:
                pass

        # Try parsing as integer if purely numeric
        if value.replace('+', '-').replace('-', '').isdigit():
            processed[new_key] = int(value.replace('+', ''))
            continue

        # Keep as string if no other type matches
        processed[new_key] = value

    return processed


def process_sph_metadata(metadata: dict[str, str]) -> dict[str, Any]:
    """
    Process SPH metadata by removing 'SPH_' prefix and converting values to appropriate types.
    Uses numpy.datetime64 for datetime values.

    :param metadata: Dictionary with SPH metadata
    :return: Processed metadata dictionary
    """
    processed: dict[str, Any] = {}

    for key, value in metadata.items():
        if not key.startswith('SPH_'):
            continue

        new_key = key[4:].lower()
        value = value.strip()

        parsed = (
                utils.try_parse_datetime(value) or
                utils.try_parse_float(value) or
                utils.try_parse_latlong(value) or
                utils.try_parse_int(value)
        )

        processed[new_key] = parsed if parsed is not None else value

    return processed


def process_ds_metadata(metadata: dict[str, str]) -> dict[str, Any]:
    """
    Process DS metadata by removing extra underscores and converting values.

    :param metadata: Dictionary with DS metadata containing underscore
    :return: Processed metadata dictionary with clean keys
    """
    processed: dict[str, Any] = {}

    for key, value in metadata.items():
        if not key.startswith('DS_'):
            continue

        # Remove DS_ prefix and clean up multiple underscores
        new_key = key[3:]  # Remove DS_ prefix
        new_key = re.sub(r'_+', '_', new_key)  # Replace multiple underscores with single
        new_key = new_key.rstrip('_')  # Remove trailing underscores
        new_key = new_key.lower()  # Convert to lowercase

        # Strip any whitespace from value
        value = value.strip()

        processed[new_key] = value

    return processed

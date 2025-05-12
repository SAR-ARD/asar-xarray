from typing import Any

import numpy as np
from osgeo import gdal

from asar_xarray import utils


def process_records_metadata(dataset: gdal.Dataset, attributes: dict[str, Any]) -> None:
    metadata = dataset.GetMetadata(domain='records')
    attributes['records'] = dict()
    attributes['records']['measurement_sq'] = process_measurement_sq_metadata(metadata)
    attributes['records']['main_processing_params'] = process_main_processing_params(metadata)
    for key, value in metadata.items():
        if "MDS1_SQ_ADS_" not in key or "CHIRP_PARAMS" not in key:
            print(f"{key}: {value}")


def process_main_processing_params(metadata: dict[str, str]) -> dict[str, Any]:
    params = dict()
    params.update(process_general_main_processing_params(metadata))
    params['raw_data_analysis'] = process_raw_data_analysis(metadata)
    return params

def process_raw_data_analysis(metadata: dict[str, str]) -> list[dict[str, Any]]:
    """
    Process raw data analysis metadata into list of dictionaries.

    :param metadata: Dictionary with raw data analysis metadata
    :return: List of dictionaries containing raw data analysis parameters
    """
    analysis_dict = {}

    for key, value in metadata.items():
        if not key.startswith('MAIN_PROCESSING_PARAMS_ADS_RAW_DATA_ANALYSIS'):
            continue

        # Split key into parts to get index and parameter name
        parts = key.split('.')
        if len(parts) != 3:
            continue

        # Get index and parameter name
        idx = int(parts[1])
        param = parts[2].lower()  # Convert parameter name to lowercase

        # Initialize dict for this index if not exists
        if idx not in analysis_dict:
            analysis_dict[idx] = {'index': idx}

        # Convert value based on type
        if param.endswith('_flag'):
            analysis_dict[idx][param] = bool(int(value))
        elif '.' in value:
            analysis_dict[idx][param] = float(value)
        else:
            analysis_dict[idx][param] = int(value)

    # Convert dictionary to the sorted list
    return [analysis_dict[idx] for idx in sorted(analysis_dict.keys())]

# def process_start_

def process_general_main_processing_params(metadata: dict[str, str]) -> dict[str, Any]:
    """
    Process basic main processing parameters metadata by removing 'MAIN_PROCESSING_PARAMS_ADS_' prefix
    and converting values to appropriate types. Excludes complex nested data structures.

    :param metadata: Dictionary with main processing parameters metadata
    :return: Processed metadata dictionary with basic parameters only
    """
    # Keys to exclude - they will be processed separately
    exclude_patterns = [
        'raw_data_analysis',
        'image_parameters',
        'bandwidth',
        'nominal_chirp',
        'calibration_factors',
        'output_statistics',
        'orbit_state_vectors',
        's_start_time',
        's_parameter_codes',
        's_error_counters',
        's_noise_estimation',
    ]

    processed = {}

    for key, value in metadata.items():
        if not key.startswith('MAIN_PROCESSING_PARAMS_ADS_'):
            continue

        # Skip excluded patterns
        if any(pattern in key.lower() for pattern in exclude_patterns):
            continue

        # Remove prefix
        new_key = key[25:].lower()

        # Strip whitespace
        value = value.strip()

        # Handle zero doppler time values
        if 'zero_doppler_time' in new_key:
            processed[new_key] = utils.get_envisat_time(value)
            continue

        # Parse flag values as booleans
        if new_key.endswith('_flag'):
            processed[new_key] = bool(int(value))
            continue

        # Parse floats
        if '.' in value:
            try:
                processed[new_key] = float(value)
                continue
            except ValueError:
                pass

        # Parse integers
        if value.replace('-', '').isdigit():
            processed[new_key] = int(value)
            continue

        # Keep strings
        processed[new_key] = value

    return processed


def process_measurement_sq_metadata(metadata: dict[str, str]) -> dict[str, Any]:
    """
    Process MDS1_SQ metadata by removing 'MDS1_SQ_ADS_' prefix and converting values to appropriate types.

    :param metadata: Dictionary with MDS1_SQ metadata
    :return: Processed metadata dictionary
    """
    processed = {}

    for key, value in metadata.items():
        if not key.startswith('MDS1_SQ_ADS_'):
            continue

        # Remove MDS1_SQ_ADS_ prefix
        new_key = key[12:].lower()

        # Strip any whitespace from value
        value = value.strip()

        # Handle zero doppler time special case (days since 2000-01-01, seconds, microseconds)
        if 'zero_doppler_time' in new_key:
            processed[new_key] = utils.get_envisat_time(value)
            continue

        # Parse flag values as booleans
        if new_key.endswith('_flag'):
            processed[new_key] = bool(int(value))
            continue

        # Try parsing as float if contains decimal point
        if '.' in value:
            try:
                # Handle space-separated float values
                values = [float(v) for v in value.split()]
                processed[new_key] = values[0] if len(values) == 1 else values
                continue
            except ValueError:
                pass

        # Try parsing as integer
        if value.replace('-', '').isdigit():
            processed[new_key] = int(value)
            continue

        # Keep as string if no other type matches
        processed[new_key] = value

    return processed

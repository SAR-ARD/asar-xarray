from typing import Any

import numpy as np
from osgeo import gdal

from asar_xarray import utils


def process_records_metadata(dataset: gdal.Dataset, attributes: dict[str, Any]) -> None:
    metadata = dataset.GetMetadata(domain='records')
    attributes['records'] = dict()
    attributes['records']['measurement_sq'] = process_measurement_sq_metadata(metadata)
    attributes['records']['main_processing_params'] = process_main_processing_params(metadata)

    done = ['MDS1_SQ_ADS_', '_BANDWIDTH', '_NOMINAL_CHIRP', 'RAW_DATA_ANALYSIS',
            'IMAGE_PARAMETERS', 'CALIBRATION_FACTORS', 'OUTPUT_STATISTICS',]
    for key, value in metadata.items():
        if not any(name in key for name in done):
            print(f"{key}: {value}")


def process_main_processing_params(metadata: dict[str, str]) -> dict[str, Any]:
    params = dict()
    params.update(process_general_main_processing_params(metadata))
    params['raw_data_analysis'] = process_raw_data_analysis(metadata)
    params['image_parameters'] = process_image_parameters(metadata)
    params['bandwidth'] = process_bandwidth(metadata)
    params['nominal_chirp'] = process_nominal_chirp(metadata)
    params['calibration_factors'] = process_calibration_factors(metadata)
    params['output_statistics'] = process_output_statistics(metadata)
    params['orbit_state_vectors'] = process_orbit_state_vectors(metadata)
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

def process_image_parameters(metadata: dict[str, str]) -> dict[str, Any]:
    """
    Process image parameters metadata by converting values to appropriate types
    and removing trailing zeros from arrays.

    :param metadata: Dictionary with image parameters metadata
    :return: Processed metadata dictionary
    """
    processed = {}

    for key, value in metadata.items():
        if not key.startswith('MAIN_PROCESSING_PARAMS_ADS_IMAGE_PARAMETERS'):
            continue

        # Get parameter name after the last dot
        param = key.split('.')[-1].lower()

        # Convert space-separated values to list of numbers
        values = [float(x) for x in value.strip().split()]

        # Remove trailing zeros (where all elements after some point are 0)
        for i in range(len(values) - 1, -1, -1):
            if values[i] != 0:
                values = values[:i + 1]
                break

        # If only one value remains, store it as scalar
        processed[param] = values[0] if len(values) == 1 else values

    return processed

def process_bandwidth(metadata: dict[str, str]) -> dict[str, Any]:
    """
    Process bandwidth metadata by extracting meaningful values.

    :param metadata: Dictionary with bandwidth metadata
    :return: Processed metadata dictionary
    """
    processed = {}

    for key, value in metadata.items():
        if not key.startswith('MAIN_PROCESSING_PARAMS_ADS_BANDWIDTH'):
            continue

        # Get parameter name after the last dot
        param = key.split('.')[-1].lower()

        # Convert space-separated values to list of numbers
        values = [float(x) for x in value.strip().split()]

        # If only one value remains, store it as scalar
        processed[param] = values[0] if len(values) == 1 else values

    return processed

def process_nominal_chirp(metadata: dict[str, str]) -> list[dict[str, Any]]:
    """
    Process nominal chirp metadata into list of dictionaries.

    :param metadata: Dictionary with nominal chirp metadata
    :return: List of dictionaries containing nominal chirp parameters
    """
    chirp_dict = {}

    for key, value in metadata.items():
        if not key.startswith('MAIN_PROCESSING_PARAMS_ADS_NOMINAL_CHIRP'):
            continue

        # Split key into parts to get index and parameter name
        parts = key.split('.')
        if len(parts) != 3:
            continue

        # Get index and parameter name
        idx = int(parts[1])
        param = parts[2].lower()  # Convert parameter name to lowercase

        # Initialize dict for this index if not exists
        if idx not in chirp_dict:
            chirp_dict[idx] = {'index': idx}

        # Convert space-separated values to list of numbers
        values = [float(x) for x in value.strip().split()]

        # Store values (or single value if list has only one element)
        chirp_dict[idx][param] = values[0] if len(values) == 1 else values

    # Convert dictionary to sorted list and filter out empty entries
    return [chirp_dict[idx] for idx in sorted(chirp_dict.keys())
            if any(v != 0 and v != [0.0] for v in chirp_dict[idx].values() if v != idx)]

def process_calibration_factors(metadata: dict[str, str]) -> list[dict[str, Any]]:
    """
    Process calibration factors metadata into list of dictionaries.

    :param metadata: Dictionary with calibration factors metadata
    :return: List of dictionaries containing calibration factors parameters
    """
    calib_dict = {}

    for key, value in metadata.items():
        if not key.startswith('MAIN_PROCESSING_PARAMS_ADS_CALIBRATION_FACTORS'):
            continue

        # Split key into parts to get index and parameter name
        parts = key.split('.')
        if len(parts) != 3:
            continue

        # Get index and parameter name
        idx = int(parts[1])
        param = parts[2].lower()  # Convert parameter name to lowercase

        # Initialize dict for this index if not exists
        if idx not in calib_dict:
            calib_dict[idx] = {'index': idx}

        # Convert value to float
        calib_dict[idx][param] = float(value.strip())

    # Convert dictionary to sorted list
    return [calib_dict[idx] for idx in sorted(calib_dict.keys())]

def process_output_statistics(metadata: dict[str, str]) -> list[dict[str, Any]]:
    """
    Process output statistics metadata into list of dictionaries.

    :param metadata: Dictionary with output statistics metadata
    :return: List of dictionaries containing output statistics parameters
    """
    stats_dict = {}

    for key, value in metadata.items():
        if not key.startswith('MAIN_PROCESSING_PARAMS_ADS_OUTPUT_STATISTICS'):
            continue

        # Split key into parts to get index and parameter name
        parts = key.split('.')
        if len(parts) != 3:
            continue

        # Get index and parameter name
        idx = int(parts[1])
        param = parts[2].lower()  # Convert parameter name to lowercase

        # Initialize dict for this index if not exists
        if idx not in stats_dict:
            stats_dict[idx] = {'index': idx}

        # Convert value to float
        stats_dict[idx][param] = float(value.strip())

    # Convert dictionary to sorted list
    return [stats_dict[idx] for idx in sorted(stats_dict.keys())]

def process_orbit_state_vectors(metadata: dict[str, str]) -> list[dict[str, Any]]:
    """
    Process orbit state vectors metadata into list of dictionaries.

    :param metadata: Dictionary with orbit state vectors metadata
    :return: List of dictionaries containing orbit state vectors parameters
    """
    vectors_dict = {}

    for key, value in metadata.items():
        if not key.startswith('MAIN_PROCESSING_PARAMS_ADS_ORBIT_STATE_VECTORS'):
            continue

        # Split key into parts to get index and parameter name
        parts = key.split('.')
        if len(parts) != 3:
            continue

        # Get index and parameter name
        idx = int(parts[1])
        param = parts[2].lower()  # Convert parameter name to lowercase

        # Initialize dict for this index if not exists
        if idx not in vectors_dict:
            vectors_dict[idx] = {'index': idx}

        # Convert time values using utils.get_envisat_time
        if 'time' in param:
            vectors_dict[idx][param] = utils.get_envisat_time(value)
        else:
            # Convert other values to int (positions and velocities)
            vectors_dict[idx][param] = int(value.strip())

    # Convert dictionary to sorted list
    return [vectors_dict[idx] for idx in sorted(vectors_dict.keys())]

def process_general_main_processing_params(metadata: dict[str, str]) -> dict[str, Any]:
    """
    Process basic main processing parameters metadata by removing 'MAIN_PROCESSING_PARAMS_ADS_' prefix
    and converting values to appropriate types. Excludes complex nested data structures.

    :param metadata: Dictionary with main processing parameters metadata
    :return: Processed metadata dictionary with basic parameters only
    """
    # Keys to exclude - they will be processed separately
    exclude_patterns = [
        'raw_data_analysis',  # done
        'image_parameters', # done
        'bandwidth', # done
        'nominal_chirp', # done
        'calibration_factors', # done
        'output_statistics', # done
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

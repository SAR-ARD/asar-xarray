"""Records metadata processing for ASAR datasets."""

from typing import Any
from osgeo import gdal

from asar_xarray import utils
from asar_xarray.utils import try_parse_float, try_parse_int, try_parse_float_list


def process_records_metadata(dataset: gdal.Dataset, attributes: dict[str, Any]) -> None:
    """
    Process metadata from a GDAL dataset and populate the attributes dictionary with structured data.

    :param dataset: GDAL dataset object containing metadata in the 'records' domain.
    :param attributes: Dictionary to store processed metadata. The 'records' key will be populated with:
        - 'measurement_sq': Processed measurement square metadata.
        - 'main_processing_params': Processed main processing parameters metadata.
        - 'dop_centroid_coeffs': Processed Doppler centroid coefficients metadata.
    """
    # Retrieve metadata from the 'records' domain of the dataset
    metadata = dataset.GetMetadata(domain='records')

    # Initialize the 'records' key in the attributes dictionary
    attributes['records'] = dict()

    # Process and store measurement square metadata
    attributes['records']['measurement_sq'] = process_measurement_sq_metadata(metadata)

    # Process and store main processing parameters metadata
    attributes['records']['main_processing_params'] = process_main_processing_params(metadata)

    # Process and store Doppler centroid coefficients metadata
    attributes['records']['dop_centroid_coeffs'] = process_dop_centroid_coeffs(metadata)


def process_main_processing_params(metadata: dict[str, str]) -> dict[str, Any]:
    """
    Process the main processing parameters metadata and organize it into a structured dictionary.

    This function extracts and processes various categories of main processing parameters
    from the provided metadata dictionary. Each category is handled by a dedicated helper function.

    :param metadata: Dictionary containing the main processing parameters metadata.
    :return: A dictionary with the processed main processing parameters, structured as follows:
        - 'general': General main processing parameters.
        - 'raw_data_analysis': List of dictionaries with raw data analysis parameters.
        - 'image_parameters': Dictionary with image parameters.
        - 'bandwidth': Dictionary with bandwidth parameters.
        - 'nominal_chirp': List of dictionaries with nominal chirp parameters.
        - 'calibration_factors': List of dictionaries with calibration factors.
        - 'output_statistics': List of dictionaries with output statistics.
        - 'orbit_state_vectors': List of dictionaries with orbit state vectors.
        - 'start_time': List of dictionaries with start time parameters.
        - 'parameter_codes': Dictionary with parameter codes.
        - 'error_counters': Dictionary with error counters.
        - 'noise_estimation': Dictionary with noise estimation parameters.
    """
    params = dict()
    params.update(process_general_main_processing_params(metadata))
    params['raw_data_analysis'] = process_raw_data_analysis(metadata)
    params['image_parameters'] = process_image_parameters(metadata)
    params['bandwidth'] = process_bandwidth(metadata)
    params['nominal_chirp'] = process_nominal_chirp(metadata)
    params['calibration_factors'] = process_calibration_factors(metadata)
    params['output_statistics'] = process_output_statistics(metadata)
    params['orbit_state_vectors'] = process_orbit_state_vectors(metadata)
    params['start_time'] = process_start_time(metadata)
    params['parameter_codes'] = process_parameter_codes(metadata)
    params['error_counters'] = process_error_counters(metadata)
    params['noise_estimation'] = process_noise_estimation(metadata)
    return params


def process_raw_data_analysis(metadata: dict[str, str]) -> list[dict[str, Any]]:
    """
    Process raw data analysis metadata into list of dictionaries.

    :param metadata: Dictionary with raw data analysis metadata
    :return: List of dictionaries containing raw data analysis parameters
    """
    analysis_dict: dict[int, dict[str, Any]] = {}

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
    Process image parameters metadata.

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
    chirp_dict: dict[int, dict[str, Any]] = {}

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
    calib_dict: dict[int, dict[str, Any]] = {}

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
    stats_dict: dict[int, dict[str, Any]] = {}

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
    vectors_dict: dict[int, dict[str, Any]] = {}

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


def process_start_time(metadata: dict[str, str]) -> list[dict[str, Any]]:
    """
    Process start time metadata into list of dictionaries.

    :param metadata: Dictionary with start time metadata
    :return: List of dictionaries containing start time parameters
    """
    time_dict: dict[int, dict[str, Any]] = {}

    for key, value in metadata.items():
        if not key.startswith('MAIN_PROCESSING_PARAMS_ADS_START_TIME'):
            continue

        # Split key into parts to get index and parameter name
        parts = key.split('.')
        if len(parts) != 3:
            continue

        # Get index and parameter name
        idx = int(parts[1])
        param = parts[2].lower()  # Convert parameter name to lowercase

        # Initialize dict for this index if not exists
        if idx not in time_dict:
            time_dict[idx] = {'index': idx}

        if param == 'first_mjd':
            # Convert MJD values using utils.get_envisat_time
            time_dict[idx][param] = utils.get_envisat_time(value)
        else:
            # Convert OBT values to tuple of integers
            time_dict[idx][param] = tuple(int(x) for x in value.split())

    # Convert dictionary to sorted list
    return [time_dict[idx] for idx in sorted(time_dict.keys())]


def process_parameter_codes(metadata: dict[str, str]) -> dict[str, Any]:
    """
    Process parameter codes metadata into dictionary.

    :param metadata: Dictionary with parameter codes metadata
    :return: Dictionary containing parameter codes
    """
    codes_dict = {}

    for key, value in metadata.items():
        if not key.startswith('MAIN_PROCESSING_PARAMS_ADS_PARAMETER_CODES'):
            continue

        # Get parameter name after last dot
        param = key.split('.')[-1].lower()

        # Convert space-separated values to list and get first non-zero value
        values = [int(x) for x in value.strip().split()]
        codes_dict[param] = values if values else 0

    return codes_dict


def process_error_counters(metadata: dict[str, str]) -> dict[str, int]:
    """
    Process error counters metadata into dictionary.

    :param metadata: Dictionary with error counters metadata
    :return: Dictionary containing error counter values
    """
    counters_dict = {}

    for key, value in metadata.items():
        if not key.startswith('MAIN_PROCESSING_PARAMS_ADS_ERROR_COUNTERS'):
            continue

        # Get parameter name after last dot
        param = key.split('.')[-1].lower()

        # Convert value to integer
        counters_dict[param] = int(value.strip())

    return counters_dict


def process_noise_estimation(metadata: dict[str, str]) -> dict[str, list[float]]:
    """
    Process noise estimation metadata into dictionary.

    :param metadata: Dictionary with noise estimation metadata
    :return: Dictionary containing noise estimation values
    """
    noise_dict = {}

    for key, value in metadata.items():
        if not key.startswith('MAIN_PROCESSING_PARAMS_ADS_NOISE_ESTIMATION'):
            continue

        # Get parameter name after last dot
        param = key.split('.')[-1].lower()

        # Convert space-separated values to list, preserving zeros
        if 'noise_power' in param:
            noise_dict[param] = [float(x) for x in value.strip().split()]
        else:
            noise_dict[param] = [int(x) for x in value.strip().split()]

    return noise_dict


def process_general_main_processing_params(metadata: dict[str, str]) -> dict[str, Any]:
    """
    Process basic main processing parameters metadata.

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
        'ads_start_time',
        's_parameter_codes',
        's_error_counters',
        's_noise_estimation',
    ]

    processed: dict[str, Any] = {}

    for key, value in metadata.items():
        if not key.startswith('MAIN_PROCESSING_PARAMS_ADS_'):
            continue
        if any(pattern in key.lower() for pattern in exclude_patterns):
            continue

        new_key = key[27:].lower()
        value = value.strip()

        # Special cases
        if 'zero_doppler_time' in new_key:
            processed[new_key] = utils.get_envisat_time(value)
        elif new_key.endswith('_flag'):
            processed[new_key] = bool(int(value))
        else:
            parsed = (
                    try_parse_float(value) or
                    try_parse_int(value)
            )
            processed[new_key] = parsed if parsed is not None else value

    return processed


def process_measurement_sq_metadata(metadata: dict[str, str]) -> dict[str, Any]:
    """
    Process MDS1_SQ metadata by removing 'MDS1_SQ_ADS_' prefix and converting values to appropriate types.

    :param metadata: Dictionary with MDS1_SQ metadata
    :return: Processed metadata dictionary
    """
    processed: dict[str, Any] = {}

    for key, value in metadata.items():
        if not key.startswith('MDS1_SQ_ADS_'):
            continue

        new_key = key[12:].lower()
        value = value.strip()

        # Special case: Zero Doppler Time
        if 'zero_doppler_time' in new_key:
            processed[new_key] = utils.get_envisat_time(value)
        # Boolean flags
        elif new_key.endswith('_flag'):
            processed[new_key] = bool(int(value))
        # Float list or single float
        else:
            parsed = (
                    try_parse_float_list(value) or
                    try_parse_float(value) or
                    try_parse_int(value)
            )
            processed[new_key] = parsed if parsed is not None else value

    return processed


def process_dop_centroid_coeffs(metadata: dict[str, str]) -> dict[str, Any]:
    """
    Process doppler centroid coefficients metadata into dictionary.

    :param metadata: Dictionary with doppler centroid coefficients metadata
    :return: Dictionary containing doppler centroid parameters
    """
    dop_dict: dict[str, Any] = {}

    for key, value in metadata.items():
        if not key.startswith('DOP_CENTROID_COEFFS_ADS_'):
            continue

        # Get parameter name after prefix
        param = key[24:].lower()

        # Process different parameter types
        if param == 'zero_doppler_time':
            dop_dict[param] = utils.get_envisat_time(value)
        elif param == 'attach_flag':
            dop_dict[param] = bool(int(value))
        elif param == 'dop_conf_below_thresh_flag':
            dop_dict[param] = bool(int(value))
        elif param in ('dop_coef', 'delta_dopp_coeff'):
            # Keep all values including zeros for coefficients
            dop_dict[param] = [float(x) for x in value.strip().split()]
        else:
            # For other numeric values
            dop_dict[param] = float(value)

    return dop_dict

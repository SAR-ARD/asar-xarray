from unittest import mock

from asar_xarray import utils
from asar_xarray.records_metadata import process_dop_centroid_coeffs, process_measurement_sq_metadata, \
    process_general_main_processing_params, process_noise_estimation, process_error_counters, process_parameter_codes, \
    process_start_time, process_orbit_state_vectors, process_output_statistics, process_calibration_factors, \
    process_nominal_chirp, process_bandwidth, process_image_parameters, process_raw_data_analysis, \
    process_main_processing_params, process_records_metadata


def test_processes_valid_doppler_coefficients_correctly():
    metadata = {
        "DOP_CENTROID_COEFFS_ADS_ZERO_DOPPLER_TIME": "647, 12, 10",
        "DOP_CENTROID_COEFFS_ADS_ATTACH_FLAG": "1",
        "DOP_CENTROID_COEFFS_ADS_DOP_CONF_BELOW_THRESH_FLAG": "0",
        "DOP_CENTROID_COEFFS_ADS_DOP_COEF": "0.1 0.2 0.3",
        "DOP_CENTROID_COEFFS_ADS_DELTA_DOPP_COEFF": "0.01 0.02"
    }
    result = process_dop_centroid_coeffs(metadata)
    assert result["zero_doppler_time"] == utils.get_envisat_time("647, 12, 10")
    assert result["attach_flag"] is True
    assert result["dop_conf_below_thresh_flag"] is False
    assert result["dop_coef"] == [0.1, 0.2, 0.3]


def test_processes_valid_measurement_sq_metadata_correctly():
    metadata = {
        "MDS1_SQ_ADS_ZERO_DOPPLER_TIME": "12345, 12, 10",
        "MDS1_SQ_ADS_VALID_FLAG": "1",
        "MDS1_SQ_ADS_FLOAT_VALUES": "0.1 0.2 0.3",
        "MDS1_SQ_ADS_INTEGER_VALUE": "42",
        "MDS1_SQ_ADS_STRING_VALUE": "example"
    }
    result = process_measurement_sq_metadata(metadata)
    assert result["zero_doppler_time"] == utils.get_envisat_time("12345, 12, 10")
    assert result["valid_flag"] is True
    assert result["float_values"] == [0.1, 0.2, 0.3]
    assert result["integer_value"] == 42
    assert result["string_value"] == "example"


def test_handles_empty_measurement_sq_metadata():
    metadata = {}
    result = process_measurement_sq_metadata(metadata)
    assert result == {}


def test_processes_single_float_value_correctly():
    metadata = {
        "MDS1_SQ_ADS_FLOAT_VALUE": "0.5"
    }
    result = process_measurement_sq_metadata(metadata)
    assert result["float_value"] == 0.5


def test_processes_boolean_flags_correctly():
    metadata = {
        "MDS1_SQ_ADS_TRUE_FLAG": "1",
        "MDS1_SQ_ADS_FALSE_FLAG": "0"
    }
    result = process_measurement_sq_metadata(metadata)
    assert result["true_flag"] is True
    assert result["false_flag"] is False


def test_processes_valid_general_main_processing_params():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_ZERO_DOPPLER_TIME": "123, 45, 678",
        "MAIN_PROCESSING_PARAMS_ADS_VALID_FLAG": "1",
        "MAIN_PROCESSING_PARAMS_ADS_FLOAT_VALUE": "0.123",
        "MAIN_PROCESSING_PARAMS_ADS_INTEGER_VALUE": "42",
        "MAIN_PROCESSING_PARAMS_ADS_STRING_VALUE": "example"
    }
    result = process_general_main_processing_params(metadata)
    assert result["zero_doppler_time"] == utils.get_envisat_time("123, 45, 678")
    assert result["valid_flag"] is True
    assert result["float_value"] == 0.123
    assert result["integer_value"] == 42
    assert result["string_value"] == "example"


def test_handles_empty_general_main_processing_params():
    metadata = {}
    result = process_general_main_processing_params(metadata)
    assert result == {}


def test_skips_excluded_patterns_in_general_main_processing_params():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_RAW_DATA_ANALYSIS.VALUE": "123",
        "MAIN_PROCESSING_PARAMS_ADS_IMAGE_PARAMETERS.VALUE": "456",
        "MAIN_PROCESSING_PARAMS_ADS_VALID_FLAG": "1"
    }
    result = process_general_main_processing_params(metadata)
    assert "raw_data_analysis.value" not in result
    assert "image_parameters.value" not in result
    assert result["valid_flag"] is True


def test_processes_boolean_flags_correctly_in_general_main_processing_params():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_T_FLAG": "1",
        "MAIN_PROCESSING_PARAMS_ADS_F_FLAG": "0"
    }
    result = process_general_main_processing_params(metadata)
    assert result["t_flag"] is True
    assert result["f_flag"] is False

def test_processes_valid_noise_estimation_metadata_correctly():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_NOISE_ESTIMATION.NOISE_POWER": "0.1 0.2 0.3",
        "MAIN_PROCESSING_PARAMS_ADS_NOISE_ESTIMATION.NOISE_LEVEL": "1 2 3"
    }
    result = process_noise_estimation(metadata)
    assert result["noise_power"] == [0.1, 0.2, 0.3]
    assert result["noise_level"] == [1, 2, 3]

def test_handles_empty_noise_estimation_metadata():
    metadata = {}
    result = process_noise_estimation(metadata)
    assert result == {}

def test_processes_single_value_noise_estimation_correctly():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_NOISE_ESTIMATION.NOISE_POWER": "0.5"
    }
    result = process_noise_estimation(metadata)
    assert result["noise_power"] == [0.5]


def test_preserves_zeros_in_noise_estimation_values():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_NOISE_ESTIMATION.NOISE_POWER": "0.0 0.1 0.0"
    }
    result = process_noise_estimation(metadata)
    assert result["noise_power"] == [0.0, 0.1, 0.0]

def test_processes_valid_error_counters_correctly():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_ERROR_COUNTERS.COUNTER_1": "10",
        "MAIN_PROCESSING_PARAMS_ADS_ERROR_COUNTERS.COUNTER_2": "20"
    }
    result = process_error_counters(metadata)
    assert result == {"counter_1": 10, "counter_2": 20}

def test_handles_empty_error_counters_metadata():
    metadata = {}
    result = process_error_counters(metadata)
    assert result == {}

def test_ignores_unrelated_metadata_keys():
    metadata = {
        "UNRELATED_KEY": "value",
        "MAIN_PROCESSING_PARAMS_ADS_ERROR_COUNTERS.COUNTER_1": "5"
    }
    result = process_error_counters(metadata)
    assert result == {"counter_1": 5}

def test_handles_invalid_integer_values_gracefully():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_ERROR_COUNTERS.COUNTER_1": "invalid"
    }
    try:
        process_error_counters(metadata)
        assert False, "Expected ValueError for invalid integer value"
    except ValueError:
        pass

def test_processes_large_integer_values_correctly():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_ERROR_COUNTERS.COUNTER_1": "2147483647"
    }
    result = process_error_counters(metadata)
    assert result == {"counter_1": 2147483647}

def test_processes_valid_parameter_codes_correctly():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_PARAMETER_CODES.CODE_1": "1 2 3",
        "MAIN_PROCESSING_PARAMS_ADS_PARAMETER_CODES.CODE_2": "4 5 6"
    }
    result = process_parameter_codes(metadata)
    assert result == {"code_1": [1, 2, 3], "code_2": [4, 5, 6]}

def test_handles_empty_parameter_codes_metadata():
    metadata = {}
    result = process_parameter_codes(metadata)
    assert result == {}

def test_handles_single_value_parameter_code():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_PARAMETER_CODES.CODE_1": "42"
    }
    result = process_parameter_codes(metadata)
    assert result == {"code_1": [42]}

def test_handles_invalid_parameter_code_values_gracefully():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_PARAMETER_CODES.CODE_1": "invalid 2"
    }
    try:
        process_parameter_codes(metadata)
        assert False, "Expected ValueError for invalid integer value"
    except ValueError:
        pass

def test_processes_parameter_codes_with_trailing_zeros():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_PARAMETER_CODES.CODE_1": "1 2 0 0"
    }
    result = process_parameter_codes(metadata)
    assert result == {"code_1": [1, 2, 0, 0]}

def test_processes_valid_start_time_metadata_correctly():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_START_TIME.1.FIRST_MJD": "12345, 12, 10",
        "MAIN_PROCESSING_PARAMS_ADS_START_TIME.1.OBT": "1 2 3",
        "MAIN_PROCESSING_PARAMS_ADS_START_TIME.2.FIRST_MJD": "54321, 34, 56",
        "MAIN_PROCESSING_PARAMS_ADS_START_TIME.2.OBT": "4 5 6"
    }
    result = process_start_time(metadata)
    assert result == [
        {"index": 1, "first_mjd": utils.get_envisat_time("12345, 12, 10"), "obt": (1, 2, 3)},
        {"index": 2, "first_mjd": utils.get_envisat_time("54321, 34, 56"), "obt": (4, 5, 6)}
    ]

def test_handles_empty_start_time_metadata():
    metadata = {}
    result = process_start_time(metadata)
    assert result == []

def test_skips_invalid_start_time_keys():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_START_TIME.INVALID_KEY": "value",
        "MAIN_PROCESSING_PARAMS_ADS_START_TIME.1.FIRST_MJD": "12345, 12, 10"
    }
    result = process_start_time(metadata)
    assert result == [
        {"index": 1, "first_mjd": utils.get_envisat_time("12345, 12, 10")}
    ]

def test_handles_invalid_obt_values_gracefully():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_START_TIME.1.OBT": "invalid"
    }
    try:
        process_start_time(metadata)
        assert False, "Expected ValueError for invalid OBT value"
    except ValueError:
        pass

def test_processes_start_time_with_missing_fields():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_START_TIME.1.FIRST_MJD": "12345, 12, 10"
    }
    result = process_start_time(metadata)
    assert result == [
        {"index": 1, "first_mjd": utils.get_envisat_time("12345, 12, 10")}
    ]

def test_processes_valid_orbit_state_vectors_correctly():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_ORBIT_STATE_VECTORS.1.POSITION_X": "1000",
        "MAIN_PROCESSING_PARAMS_ADS_ORBIT_STATE_VECTORS.1.POSITION_Y": "2000",
        "MAIN_PROCESSING_PARAMS_ADS_ORBIT_STATE_VECTORS.1.POSITION_Z": "3000",
        "MAIN_PROCESSING_PARAMS_ADS_ORBIT_STATE_VECTORS.1.TIME": "12345, 12, 10"
    }
    result = process_orbit_state_vectors(metadata)
    assert result == [
        {
            "index": 1,
            "position_x": 1000,
            "position_y": 2000,
            "position_z": 3000,
            "time": utils.get_envisat_time("12345, 12, 10")
        }
    ]

def test_handles_empty_orbit_state_vectors_metadata():
    metadata = {}
    result = process_orbit_state_vectors(metadata)
    assert result == []

def test_skips_invalid_orbit_state_vector_keys():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_ORBIT_STATE_VECTORS.INVALID_KEY": "value",
        "MAIN_PROCESSING_PARAMS_ADS_ORBIT_STATE_VECTORS.1.POSITION_X": "1000"
    }
    result = process_orbit_state_vectors(metadata)
    assert result == [
        {
            "index": 1,
            "position_x": 1000
        }
    ]

def test_handles_invalid_time_values_gracefully():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_ORBIT_STATE_VECTORS.1.TIME": "invalid"
    }
    try:
        process_orbit_state_vectors(metadata)
        assert False, "Expected ValueError for invalid time value"
    except ValueError:
        pass

def test_processes_orbit_state_vectors_with_missing_fields():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_ORBIT_STATE_VECTORS.1.POSITION_X": "1000"
    }
    result = process_orbit_state_vectors(metadata)
    assert result == [
        {
            "index": 1,
            "position_x": 1000
        }
    ]

def test_processes_valid_output_statistics_correctly():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_OUTPUT_STATISTICS.1.VALUE_A": "0.1",
        "MAIN_PROCESSING_PARAMS_ADS_OUTPUT_STATISTICS.1.VALUE_B": "0.2",
        "MAIN_PROCESSING_PARAMS_ADS_OUTPUT_STATISTICS.2.VALUE_A": "1.5",
        "MAIN_PROCESSING_PARAMS_ADS_OUTPUT_STATISTICS.2.VALUE_B": "2.5"
    }
    result = process_output_statistics(metadata)
    assert result == [
        {"index": 1, "value_a": 0.1, "value_b": 0.2},
        {"index": 2, "value_a": 1.5, "value_b": 2.5}
    ]

def test_handles_empty_output_statistics_metadata():
    metadata = {}
    result = process_output_statistics(metadata)
    assert result == []

def test_skips_invalid_output_statistics_keys():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_OUTPUT_STATISTICS.INVALID_KEY": "value",
        "MAIN_PROCESSING_PARAMS_ADS_OUTPUT_STATISTICS.1.VALUE_A": "0.1"
    }
    result = process_output_statistics(metadata)
    assert result == [
        {"index": 1, "value_a": 0.1}
    ]

def test_handles_invalid_output_statistics_values_gracefully():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_OUTPUT_STATISTICS.1.VALUE_A": "invalid"
    }
    try:
        process_output_statistics(metadata)
        assert False, "Expected ValueError for invalid float value"
    except ValueError:
        pass

def test_processes_output_statistics_with_missing_fields():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_OUTPUT_STATISTICS.1.VALUE_A": "0.1"
    }
    result = process_output_statistics(metadata)
    assert result == [
        {"index": 1, "value_a": 0.1}
    ]

def test_processes_valid_calibration_factors_correctly():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_CALIBRATION_FACTORS.1.FACTOR_A": "1.23",
        "MAIN_PROCESSING_PARAMS_ADS_CALIBRATION_FACTORS.1.FACTOR_B": "4.56",
        "MAIN_PROCESSING_PARAMS_ADS_CALIBRATION_FACTORS.2.FACTOR_A": "7.89"
    }
    result = process_calibration_factors(metadata)
    assert result == [
        {"index": 1, "factor_a": 1.23, "factor_b": 4.56},
        {"index": 2, "factor_a": 7.89}
    ]

def test_handles_empty_calibration_factors_metadata():
    metadata = {}
    result = process_calibration_factors(metadata)
    assert result == []

def test_skips_invalid_calibration_factors_keys():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_CALIBRATION_FACTORS.INVALID_KEY": "value",
        "MAIN_PROCESSING_PARAMS_ADS_CALIBRATION_FACTORS.1.FACTOR_A": "1.23"
    }
    result = process_calibration_factors(metadata)
    assert result == [
        {"index": 1, "factor_a": 1.23}
    ]

def test_handles_invalid_calibration_factors_values_gracefully():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_CALIBRATION_FACTORS.1.FACTOR_A": "invalid"
    }
    try:
        process_calibration_factors(metadata)
        assert False, "Expected ValueError for invalid float value"
    except ValueError:
        pass

def test_processes_calibration_factors_with_missing_fields():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_CALIBRATION_FACTORS.1.FACTOR_A": "1.23"
    }
    result = process_calibration_factors(metadata)
    assert result == [
        {"index": 1, "factor_a": 1.23}
    ]

def test_processes_valid_nominal_chirp_metadata_correctly():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_NOMINAL_CHIRP.1.PARAM_A": "0.1 0.2 0.3",
        "MAIN_PROCESSING_PARAMS_ADS_NOMINAL_CHIRP.1.PARAM_B": "1.5",
        "MAIN_PROCESSING_PARAMS_ADS_NOMINAL_CHIRP.2.PARAM_A": "2.0 3.0"
    }
    result = process_nominal_chirp(metadata)
    assert result == [
        {"index": 1, "param_a": [0.1, 0.2, 0.3], "param_b": 1.5},
        {"index": 2, "param_a": [2.0, 3.0]}
    ]

def test_handles_empty_nominal_chirp_metadata():
    metadata = {}
    result = process_nominal_chirp(metadata)
    assert result == []

def test_skips_invalid_nominal_chirp_keys():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_NOMINAL_CHIRP.INVALID_KEY": "value",
        "MAIN_PROCESSING_PARAMS_ADS_NOMINAL_CHIRP.1.PARAM_A": "0.1"
    }
    result = process_nominal_chirp(metadata)
    assert result == [
        {"index": 1, "param_a": 0.1}
    ]

def test_handles_invalid_nominal_chirp_values_gracefully():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_NOMINAL_CHIRP.1.PARAM_A": "invalid"
    }
    try:
        process_nominal_chirp(metadata)
        assert False, "Expected ValueError for invalid float value"
    except ValueError:
        pass

def test_processes_nominal_chirp_with_missing_fields():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_NOMINAL_CHIRP.1.PARAM_A": "0.1"
    }
    result = process_nominal_chirp(metadata)
    assert result == [
        {"index": 1, "param_a": 0.1}
    ]

def test_processes_valid_bandwidth_metadata_correctly():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_BANDWIDTH.PARAM_A": "0.1 0.2 0.3",
        "MAIN_PROCESSING_PARAMS_ADS_BANDWIDTH.PARAM_B": "1.5"
    }
    result = process_bandwidth(metadata)
    assert result == {
        "param_a": [0.1, 0.2, 0.3],
        "param_b": 1.5
    }

def test_handles_empty_bandwidth_metadata():
    metadata = {}
    result = process_bandwidth(metadata)
    assert result == {}

def test_handles_single_value_bandwidth_correctly():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_BANDWIDTH.PARAM_A": "0.5"
    }
    result = process_bandwidth(metadata)
    assert result == {
        "param_a": 0.5
    }

def test_handles_invalid_bandwidth_values_gracefully():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_BANDWIDTH.PARAM_A": "invalid"
    }
    try:
        process_bandwidth(metadata)
        assert False, "Expected ValueError for invalid float value"
    except ValueError:
        pass

def test_processes_valid_image_parameters_correctly():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_IMAGE_PARAMETERS.PARAM_A": "0.1 0.2 0.3",
        "MAIN_PROCESSING_PARAMS_ADS_IMAGE_PARAMETERS.PARAM_B": "1.5"
    }
    result = process_image_parameters(metadata)
    assert result == {
        "param_a": [0.1, 0.2, 0.3],
        "param_b": 1.5
    }

def test_handles_empty_image_parameters_metadata():
    metadata = {}
    result = process_image_parameters(metadata)
    assert result == {}

def test_does_not_remove_trailing_zeros_from_image_parameters():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_IMAGE_PARAMETERS.PARAM_A": "0.1 0.2 0.0 0.0",
        "MAIN_PROCESSING_PARAMS_ADS_IMAGE_PARAMETERS.PARAM_B": "1.0 0.0"
    }
    result = process_image_parameters(metadata)
    assert result == {
        "param_a": [0.1, 0.2, 0.0, 0.0],
        "param_b": [1.0, 0.0]
    }

def test_handles_single_value_image_parameters_correctly():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_IMAGE_PARAMETERS.PARAM_A": "0.5"
    }
    result = process_image_parameters(metadata)
    assert result == {
        "param_a": 0.5
    }

def test_handles_invalid_image_parameters_gracefully():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_IMAGE_PARAMETERS.PARAM_A": "invalid"
    }
    try:
        process_image_parameters(metadata)
        assert False, "Expected ValueError for invalid float value"
    except ValueError:
        pass

def test_processes_valid_raw_data_analysis_correctly():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_RAW_DATA_ANALYSIS.1.PARAM_A": "1.23",
        "MAIN_PROCESSING_PARAMS_ADS_RAW_DATA_ANALYSIS.1.PARAM_B": "4",
        "MAIN_PROCESSING_PARAMS_ADS_RAW_DATA_ANALYSIS.2.PARAM_A": "5.67",
        "MAIN_PROCESSING_PARAMS_ADS_RAW_DATA_ANALYSIS.2.PARAM_FLAG": "1"
    }
    result = process_raw_data_analysis(metadata)
    assert result == [
        {"index": 1, "param_a": 1.23, "param_b": 4},
        {"index": 2, "param_a": 5.67, "param_flag": True}
    ]

def test_handles_empty_raw_data_analysis_metadata():
    metadata = {}
    result = process_raw_data_analysis(metadata)
    assert result == []

def test_skips_invalid_raw_data_analysis_keys():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_RAW_DATA_ANALYSIS.INVALID_KEY": "value",
        "MAIN_PROCESSING_PARAMS_ADS_RAW_DATA_ANALYSIS.1.PARAM_A": "1.23"
    }
    result = process_raw_data_analysis(metadata)
    assert result == [
        {"index": 1, "param_a": 1.23}
    ]

def test_handles_invalid_raw_data_analysis_values_gracefully():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_RAW_DATA_ANALYSIS.1.PARAM_A": "invalid"
    }
    try:
        process_raw_data_analysis(metadata)
        assert False, "Expected ValueError for invalid numeric value"
    except ValueError:
        pass

def test_processes_raw_data_analysis_with_missing_fields():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_RAW_DATA_ANALYSIS.1.PARAM_FLAG": "0"
    }
    result = process_raw_data_analysis(metadata)
    assert result == [
        {"index": 1, "param_flag": False}
    ]

def test_processes_all_main_processing_params_correctly():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_RAW_DATA_ANALYSIS.1.PARAM_A": "4.56",
        "MAIN_PROCESSING_PARAMS_ADS_IMAGE_PARAMETERS.PARAM_A": "0.1 0.2",
        "MAIN_PROCESSING_PARAMS_ADS_BANDWIDTH.PARAM_A": "0.5",
        "MAIN_PROCESSING_PARAMS_ADS_NOMINAL_CHIRP.1.PARAM_A": "2.0",
        "MAIN_PROCESSING_PARAMS_ADS_CALIBRATION_FACTORS.1.FACTOR_A": "3.14",
        "MAIN_PROCESSING_PARAMS_ADS_OUTPUT_STATISTICS.1.VALUE_A": "0.01",
        "MAIN_PROCESSING_PARAMS_ADS_ORBIT_STATE_VECTORS.1.POSITION_X": "1000",
        "MAIN_PROCESSING_PARAMS_ADS_START_TIME.1.FIRST_MJD": "12345, 12, 10",
        "MAIN_PROCESSING_PARAMS_ADS_PARAMETER_CODES.CODE_1": "42",
        "MAIN_PROCESSING_PARAMS_ADS_ERROR_COUNTERS.COUNTER_1": "5",
        "MAIN_PROCESSING_PARAMS_ADS_NOISE_ESTIMATION.NOISE_POWER": "0.1 0.2"
    }
    result = process_main_processing_params(metadata)
    assert result["raw_data_analysis"] == [{"index": 1, "param_a": 4.56}]
    assert result["image_parameters"]["param_a"] == [0.1, 0.2]
    assert result["bandwidth"]["param_a"] == 0.5
    assert result["nominal_chirp"] == [{"index": 1, "param_a": 2.0}]
    assert result["calibration_factors"] == [{"index": 1, "factor_a": 3.14}]
    assert result["output_statistics"] == [{"index": 1, "value_a": 0.01}]
    assert result["orbit_state_vectors"] == [{"index": 1, "position_x": 1000}]
    assert result["start_time"] == [{"index": 1, "first_mjd": utils.get_envisat_time("12345, 12, 10")}]
    assert result["parameter_codes"]["code_1"] == [42]
    assert result["error_counters"]["counter_1"] == 5
    assert result["noise_estimation"]["noise_power"] == [0.1, 0.2]

def test_handles_empty_main_processing_params_metadata():
    metadata = {}
    result = process_main_processing_params(metadata)
    assert result == {
        "raw_data_analysis": [],
        "image_parameters": {},
        "bandwidth": {},
        "nominal_chirp": [],
        "calibration_factors": [],
        "output_statistics": [],
        "orbit_state_vectors": [],
        "start_time": [],
        "parameter_codes": {},
        "error_counters": {},
        "noise_estimation": {}
    }

def test_skips_invalid_keys_in_main_processing_params():
    metadata = {
        "INVALID_KEY": "value",
        "MAIN_PROCESSING_PARAMS_ADS_GENERAL.PARAM_A": "1.23"
    }
    result = process_main_processing_params(metadata)
    assert "invalid_key" not in result
    assert result["general.param_a"] == 1.23

def test_handles_invalid_values_gracefully_in_main_processing_params():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_RAW_DATA_ANALYSIS.1.PARAM_A": "invalid"
    }
    try:
        process_main_processing_params(metadata)
        assert False, "Expected ValueError for invalid numeric value"
    except ValueError:
        pass

def test_processes_main_processing_params_with_missing_fields():
    metadata = {
        "MAIN_PROCESSING_PARAMS_ADS_RAW_DATA_ANALYSIS.1.PARAM_FLAG": "1"
    }
    result = process_main_processing_params(metadata)
    assert result["raw_data_analysis"] == [{"index": 1, "param_flag": True}]

def test_processes_records_metadata_correctly():
    dataset = mock.Mock()
    dataset.GetMetadata.return_value = {
        "MDS1_SQ_ADS_PARAM_A": "1.23",
        "MAIN_PROCESSING_PARAMS_ADS_GENERAL.PARAM_A": "4.56",
        "DOP_CENTROID_COEFFS_ADS_ZERO_DOPPLER_TIME": "12345, 12, 10"
    }
    attributes = {}
    process_records_metadata(dataset, attributes)
    assert attributes["records"]["measurement_sq"]["param_a"] == 1.23
    assert attributes["records"]["main_processing_params"]["general.param_a"] == 4.56
    assert attributes["records"]["dop_centroid_coeffs"]["zero_doppler_time"] == utils.get_envisat_time("12345, 12, 10")

def test_handles_empty_records_metadata():
    dataset = mock.Mock()
    dataset.GetMetadata.return_value = {}
    attributes = {}
    process_records_metadata(dataset, attributes)
    assert attributes["records"]["measurement_sq"] == {}
    assert attributes["records"]["main_processing_params"] == {
        "raw_data_analysis": [],
        "image_parameters": {},
        "bandwidth": {},
        "nominal_chirp": [],
        "calibration_factors": [],
        "output_statistics": [],
        "orbit_state_vectors": [],
        "start_time": [],
        "parameter_codes": {},
        "error_counters": {},
        "noise_estimation": {}
    }
    assert attributes["records"]["dop_centroid_coeffs"] == {}

def stest_kips_invalid_records_metadata_keys():
    dataset = mock.Mock()
    dataset.GetMetadata.return_value = {
        "INVALID_KEY": "value",
        "MDS1_SQ_ADS_PARAM_A": "1.23"
    }
    attributes = {}
    process_records_metadata(dataset, attributes)
    assert "invalid_key" not in attributes["records"]
    assert attributes["records"]["measurement_sq"]["param_a"] == 1.23
from typing import Any

import numpy as np
from datetime import datetime

from asar_xarray.general_metadata import process_mph_metadata, process_sph_metadata, process_ds_metadata, \
    process_general_metadata
from tests.utils import mock_gdal_dataset


def test_processes_mph_metadata_correctly() -> None:
    metadata = {
        "MPH_CREATION_DATE": "01-JAN-2023 12:00:00.000",
        "MPH_ORBIT_NUMBER": "12345",
        "MPH_SATELLITE": "SAT-A",
        "MPH_FLOAT_VALUE": "1.23e4",
        "MPH_INTEGER_VALUE": "+42",
        "MPH_STRING_VALUE": "Test String"
    }
    result = process_mph_metadata(metadata)
    assert result["creation_date"] == np.datetime64(datetime(2023, 1, 1, 12, 0, 0), "ns")
    assert result["orbit_number"] == 12345
    assert result["satellite"] == "SAT-A"
    assert np.isclose(result["float_value"], 12300.0, rtol=1e-09, atol=1e-09)
    assert result["integer_value"] == 42
    assert result["string_value"] == "Test String"


def test_ignores_non_mph_keys() -> None:
    metadata = {
        "NON_MPH_KEY": "value",
        "MPH_VALID_KEY": "123"
    }
    result = process_mph_metadata(metadata)
    assert "non_mph_key" not in result
    assert "valid_key" in result


def test_handles_empty_metadata() -> None:
    metadata: [str, Any] = {}
    result = process_mph_metadata(metadata)
    assert result == {}


def test_handles_whitespace_in_values() -> None:
    metadata = {
        "MPH_KEY_WITH_SPACES": "   123   "
    }
    result = process_mph_metadata(metadata)
    assert result["key_with_spaces"] == 123


def test_processes_sph_metadata_correctly() -> None:
    metadata = {
        "SPH_CREATION_DATE": "01-JAN-2023 12:00:00.000",
        "SPH_ORBIT_NUMBER": "12345",
        "SPH_SATELLITE": "SAT-B",
        "SPH_FLOAT_VALUE": "1.23e4",
        "SPH_INTEGER_VALUE": "+42",
        "SPH_STRING_VALUE": "Test String"
    }
    result = process_sph_metadata(metadata)
    assert result["creation_date"] == np.datetime64(datetime(2023, 1, 1, 12, 0, 0), "ns")
    assert result["orbit_number"] == 12345
    assert result["satellite"] == "SAT-B"
    assert np.isclose(result["float_value"], 12300.0, rtol=1e-09, atol=1e-09)
    assert result["integer_value"] == 42
    assert result["string_value"] == "Test String"


def test_ignores_non_sph_keys() -> None:
    metadata = {
        "NON_SPH_KEY": "value",
        "SPH_VALID_KEY": "123"
    }
    result = process_sph_metadata(metadata)
    assert "non_sph_key" not in result
    assert "valid_key" in result


def test_handles_empty_sph_metadata() -> None:
    metadata: [str, Any] = {}
    result = process_sph_metadata(metadata)
    assert result == {}


def test_parses_lat_long_values_correctly() -> None:
    metadata = {
        "SPH_LATITUDE": "+1234567890",
        "SPH_LONGITUDE": "-0987654321"
    }
    result = process_sph_metadata(metadata)
    assert np.isclose(result["latitude"], 123.456789, rtol=1e-09, atol=1e-09)
    assert np.isclose(result["longitude"], -98.7654321, rtol=1e-09, atol=1e-09)


def test_handles_whitespace_in_sph_values() -> None:
    metadata = {
        "SPH_KEY_WITH_SPACES": "   123   "
    }
    result = process_sph_metadata(metadata)
    assert result["key_with_spaces"] == 123


def test_processes_ds_metadata_correctly() -> None:
    metadata = {
        "DS_KEY_ONE": "Value1",
        "DS_KEY_TWO": "Value2"
    }
    result = process_ds_metadata(metadata)
    assert result["key_one"] == "Value1"
    assert result["key_two"] == "Value2"


def test_ignores_non_ds_keys() -> None:
    metadata = {
        "NON_DS_KEY": "Value",
        "DS_VALID_KEY": "ValidValue"
    }
    result = process_ds_metadata(metadata)
    assert "non_ds_key" not in result
    assert result["valid_key"] == "ValidValue"


def test_handles_empty_ds_metadata() -> None:
    metadata: [str, Any] = {}
    result = process_ds_metadata(metadata)
    assert result == {}


def test_removes_extra_underscores_in_keys() -> None:
    metadata = {
        "DS_KEY__WITH__EXTRA___UNDERSCORES_": "Value"
    }
    result = process_ds_metadata(metadata)
    assert result["key_with_extra_underscores"] == "Value"


def test_strips_whitespace_from_values() -> None:
    metadata = {
        "DS_KEY_WITH_SPACES": "   Value   "
    }
    result = process_ds_metadata(metadata)
    assert result["key_with_spaces"] == "Value"


def test_processes_general_metadata_correctly() -> None:
    dataset = mock_gdal_dataset({
        "MPH_CREATION_DATE": "01-JAN-2023 12:00:00.000",
        "SPH_LATITUDE": "+1234567890",
        "DS_KEY_ONE": "Value1"
    })
    attributes = {}
    process_general_metadata(dataset, attributes)
    assert attributes["creation_date"] == np.datetime64(datetime(2023, 1, 1, 12, 0, 0), "ns")
    assert np.isclose(attributes["latitude"], 123.456789, rtol=1e-09, atol=1e-09)
    assert attributes["key_one"] == "Value1"


def test_handles_empty_metadata_in_general_processing() -> None:
    dataset = mock_gdal_dataset({})
    attributes = {}
    process_general_metadata(dataset, attributes)
    assert attributes == {}


def test_ignores_unrelated_metadata_keys() -> None:
    dataset = mock_gdal_dataset({
        "UNRELATED_KEY": "value",
        "MPH_VALID_KEY": "123"
    })
    attributes = {}
    process_general_metadata(dataset, attributes)
    assert "unrelated_key" not in attributes
    assert attributes["valid_key"] == 123


def test_processes_combined_metadata_correctly() -> None:
    dataset = mock_gdal_dataset({
        "MPH_CREATION_DATE": "01-JAN-2023 12:00:00.000",
        "SPH_LONGITUDE": "-0987654321",
        "DS_KEY_WITH_SPACES": "   Value   "
    })
    attributes = {}
    process_general_metadata(dataset, attributes)
    assert attributes["creation_date"] == np.datetime64(datetime(2023, 1, 1, 12, 0, 0), "ns")
    assert np.isclose(attributes["longitude"], -98.7654321, rtol=1e-09, atol=1e-09)
    assert attributes["key_with_spaces"] == "Value"

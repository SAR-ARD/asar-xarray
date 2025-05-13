from asar_xarray.derived_subdatasets_metadata import process_derived_subdatasets_metadata
from tests.utils import mock_gdal_dataset


def test_processes_derived_subdatasets_metadata_correctly():
    dataset = mock_gdal_dataset({
        "DERIVED_SUBDATASETS_1_NAME": "SUBDATASET:amplitude:/path/to/amplitude",
        "DERIVED_SUBDATASETS_1_DESC": "Amplitude data",
        "DERIVED_SUBDATASETS_2_NAME": "SUBDATASET:phase:/path/to/phase",
        "DERIVED_SUBDATASETS_2_DESC": "Phase data"
    })
    attributes = {}
    process_derived_subdatasets_metadata(dataset, attributes)
    assert attributes["derived_subdatasets"] == [
        {"operation": "amplitude", "filepath": "/path/to/amplitude", "description": "Amplitude data"},
        {"operation": "phase", "filepath": "/path/to/phase", "description": "Phase data"}
    ]

def test_handles_empty_derived_subdatasets_metadata():
    dataset = mock_gdal_dataset({})
    attributes = {}
    process_derived_subdatasets_metadata(dataset, attributes)
    assert attributes["derived_subdatasets"] == []
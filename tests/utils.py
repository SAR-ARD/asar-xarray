from typing import Any
from unittest.mock import Mock

from osgeo import gdal


def mock_gdal_dataset(metadata: dict[str, Any]) -> Mock:
    """
    Creates a mock GDAL dataset that returns the specified metadata when GetMetadata is called.

    :param metadata: Dictionary containing the metadata to be returned
    :return: Mock object simulating a GDAL dataset
    """
    mock_dataset = Mock(spec=gdal.Dataset)
    mock_dataset.GetMetadata.return_value = metadata
    return mock_dataset

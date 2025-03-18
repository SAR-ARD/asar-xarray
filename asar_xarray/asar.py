import os
from typing import Dict, Any

import xarray as xr
import numpy as np
from osgeo import gdal
from xarray.backends import AbstractDataStore
from xarray.core.types import ReadBuffer

from asar_xarray import reader


def get_attributes(gdal_dataset: gdal.Dataset) -> Dict[str, Any]:
    """
    Build xarray attributes from gdal dataset to be used in xarray.

    :param gdal_dataset: Dataset with metadata
    :return: Dictionary with metadata attributes
    """
    attributes = dict(name=gdal_dataset.GetMetadata())

    return attributes


def open_asar_dataset(filepath: str | os.PathLike[Any] | ReadBuffer[Any] | AbstractDataStore) -> xr.Dataset:
    if not isinstance(filepath, str):
        raise NotImplementedError(f'Filepath type {type(filepath)} is not supported')
    gdal_dataset: gdal.Dataset = reader.get_gdal_dataset(filepath)
    attributes = get_attributes(gdal_dataset)
    data = gdal_dataset.ReadAsArray()
    dataset: xr.Dataset = xr.Dataset(data_vars={'pixel_values': (('y', 'x'), data)},
                                     coords={
                                         'x': np.arange(data.shape[1]),
                                         'y': np.arange(data.shape[0])
                                     }, attrs=attributes)
    return dataset

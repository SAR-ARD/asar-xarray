import os
from typing import Dict, Any

import xarray as xr
import numpy as np
from osgeo import gdal
from xarray.backends import AbstractDataStore
from xarray.core.types import ReadBuffer
from asar_xarray import reader, utils
from loguru import logger


def get_attributes(gdal_dataset: gdal.Dataset) -> Dict[str, Any]:
    """
    Build xarray attributes from gdal dataset to be used in xarray.

    :param gdal_dataset: Dataset with metadata
    :return: Dictionary with metadata attributes
    """
    attributes = dict()
    attributes['antenna_elevation_pattern'] = get_antenna_elevation_pattern(gdal_dataset)
    attributes['chirp_parameters'] = get_chirp_parameters(gdal_dataset)
    attributes['orbit_state_vectors'] = get_orbit_state_vectors(gdal_dataset)

    return attributes


def open_asar_dataset(filepath: str | os.PathLike[Any] | ReadBuffer[Any] | AbstractDataStore) -> xr.Dataset:
    if not isinstance(filepath, str):
        raise NotImplementedError(f'Filepath type {type(filepath)} is not supported')
    logger.debug('Opening ASAR dataset %s', filepath)
    gdal_dataset: gdal.Dataset = reader.get_gdal_dataset(filepath)
    attributes = get_attributes(gdal_dataset)
    data = gdal_dataset.ReadAsArray()
    dataset: xr.Dataset = xr.Dataset(data_vars={'pixel_values': (('y', 'x'), data)},
                                     coords={
                                         'x': np.arange(data.shape[1]),
                                         'y': np.arange(data.shape[0])
                                     }, attrs=attributes)
    return dataset

def get_orbit_state_vectors(gdal_dataset: gdal.Dataset) -> dict[str, Any]:
    return dict()

def get_antenna_elevation_pattern(dataset: gdal.Dataset) -> dict[str, Any]:
    return dict()


def get_chirp_parameters(dataset: gdal.Dataset) -> dict[str, Any]:
    """
    Parses dataset metadata for chirp parameters.
    :param dataset: ASAR dataset.
    :return: dictionary with chirp parameters.
    """
    domains = dataset.GetMetadataDomainList()
    # TODO(Anton): remove print statements
    for domain in domains:
        print("\n")
        print(domain)
        print(dataset.GetMetadata(domain))
    print(dataset.GetMetadataDomainList())
    metadata = dataset.GetMetadata(domain='RECORDS')
    params = dict()
    # Non-float values
    params['zero_doppler_time'] = utils.get_mjd(metadata.get('CHIRP_PARAMS_ADS_ZERO_DOPPLER_TIME'))
    params['attach_flag'] = bool(int(metadata.get('CHIRP_PARAMS_ADS_ATTACH_FLAG', '0')))
    params['beam_id'] = metadata.get('CHIRP_PARAMS_ADS_BEAM_ID')
    params['polarisation'] = metadata.get('CHIRP_PARAMS_ADS_POLAR')
    params['chirp'] = dict()
    for key, value in metadata.items():
        if 'CHIRP_PARAMS_ADS_CHIRP' in key:
            new_key = key.replace('CHIRP_PARAMS_ADS_CHIRP_', '')
            params['chirp'][new_key] = float(value)
        print(key, value)

    return params

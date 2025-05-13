import os
from typing import Dict, Any

import xarray as xr
import numpy as np
from osgeo import gdal
from xarray.backends import AbstractDataStore
from xarray.core.types import ReadBuffer
from asar_xarray import reader, utils
from loguru import logger

from asar_xarray.derived_subdatasets_metadata import process_derived_subdatasets_metadata
from asar_xarray.general_metadata import process_general_metadata
from asar_xarray.records_metadata import process_records_metadata


def get_attributes(gdal_dataset: gdal.Dataset) -> Dict[str, Any]:
    """
    Build xarray attributes from gdal dataset to be used in xarray.

    :param gdal_dataset: Dataset with metadata
    :return: Dictionary with metadata attributes
    """
    attributes = dict()
    process_general_metadata(gdal_dataset, attributes)
    process_records_metadata(gdal_dataset, attributes)
    process_derived_subdatasets_metadata(gdal_dataset, attributes)


    attributes['chirp_parameters'] = get_chirp_parameters(gdal_dataset)

    return attributes


def open_asar_dataset(filepath: str | os.PathLike[Any] | ReadBuffer[Any] | AbstractDataStore) -> xr.Dataset:
    if not isinstance(filepath, str):
        raise NotImplementedError(f'Filepath type {type(filepath)} is not supported')
    logger.debug('Opening ASAR dataset {}', filepath)
    gdal_dataset: gdal.Dataset = reader.get_gdal_dataset(filepath)
    attributes = get_attributes(gdal_dataset)
    data = gdal_dataset.ReadAsArray()
    dataset: xr.Dataset = xr.Dataset(data_vars={'pixel_values': (('y', 'x'), data)},
                                     coords={
                                         'x': np.arange(data.shape[1]),
                                         'y': np.arange(data.shape[0])
                                     }, attrs=attributes)
    return dataset


def get_chirp_parameters(dataset: gdal.Dataset) -> dict[str, Any]:
    """
    Parses dataset metadata for chirp parameters.
    :param dataset: ASAR dataset.
    :return: dictionary with chirp parameters.
    """
    metadata = dataset.GetMetadata(domain='RECORDS')
    params = dict()
    # Non-float values
    params['zero_doppler_time'] = utils.get_envisat_time(metadata.get('CHIRP_PARAMS_ADS_ZERO_DOPPLER_TIME'))
    params['attach_flag'] = bool(int(metadata.get('CHIRP_PARAMS_ADS_ATTACH_FLAG', '0')))
    params['beam_id'] = metadata.get('CHIRP_PARAMS_ADS_BEAM_ID')
    params['polarisation'] = metadata.get('CHIRP_PARAMS_ADS_POLAR')
    params['chirp'] = dict()
    for key, value in metadata.items():
        if 'CHIRP_PARAMS_ADS_CHIRP' in key:
            new_key = key.replace('CHIRP_PARAMS_ADS_CHIRP_', '').lower()
            params['chirp'][new_key] = float(value)

    params['elev_corr_factor'] = float(metadata.get('CHIRP_PARAMS_ADS_ELEV_CORR_FACTOR'))
    params['cal_pulse_info'] = get_chirp_cal_pulse_info(metadata)

    return params


def get_chirp_cal_pulse_info(metadata: dict[str, str]) -> list[dict]:
    """
    Parse calibration pulse information from metadata into list of dictionaries.

    :param metadata: Dictionary containing metadata with CAL_PULSE_INFO entries
    :return: List of dictionaries containing calibration pulse parameters
    """
    cal_info_dict = {}

    for key, value in metadata.items():
        if 'CAL_PULSE_INFO' not in key:
            continue

        # Split key into parts: idx and parameter
        parts = key.split('.')
        if len(parts) < 3:
            continue

        idx = parts[1]  # Get the index number
        param = parts[2]  # Get parameter name

        # Initialize dict for this index if not exists
        if idx not in cal_info_dict:
            cal_info_dict[idx] = {'index': idx}

        # Convert values to float, handling multiple values
        values = [float(v) for v in value.split()]

        # Store single values directly, lists as lists
        if len(values) == 1:
            cal_info_dict[idx][param] = values[0]
        else:
            cal_info_dict[idx][param] = values

    # Convert the dictionary of dictionaries to the list of dictionaries
    return list(cal_info_dict.values())

"""ASAR Xarray Dataset Reader."""

import os
from typing import Dict, Any

import pandas as pd
import xarray as xr
import numpy as np
from osgeo import gdal
from xarray.backends import AbstractDataStore
from xarray.core.types import ReadBuffer
from asar_xarray import reader, utils, envisat_direct
from loguru import logger

from asar_xarray.derived_subdatasets_metadata import process_derived_subdatasets_metadata
from asar_xarray.general_metadata import process_general_metadata
from asar_xarray.records_metadata import process_records_metadata


def get_metadata(gdal_dataset: gdal.Dataset) -> Dict[str, Any]:
    """
    Build xarray attributes from gdal dataset to be used in xarray.

    :param gdal_dataset: Dataset with metadata
    :return: Dictionary with metadata attributes
    """
    attributes: dict[str, Any] = dict()
    process_general_metadata(gdal_dataset, attributes)
    process_records_metadata(gdal_dataset, attributes)
    process_derived_subdatasets_metadata(gdal_dataset, attributes)

    attributes['chirp_parameters'] = get_chirp_parameters(gdal_dataset)

    return attributes


def open_asar_dataset(filepath: str | os.PathLike[Any] | ReadBuffer[Any] | AbstractDataStore) -> xr.Dataset:
    """
    Open an ASAR dataset and converts it into an xarray Dataset.

    This function reads the metadata and pixel data from the given ASAR dataset file,
    processes the metadata into attributes, and constructs an xarray Dataset.

    :param filepath: The path to the ASAR dataset file. It can be a string,
                     a PathLike object, a ReadBuffer, or an AbstractDataStore.
    :return: An xarray Dataset containing the pixel data and metadata attributes.
    :raises NotImplementedError: If the filepath is not a string.
    """
    if not isinstance(filepath, str):
        raise NotImplementedError(f'Filepath type {type(filepath)} is not supported')

    logger.debug('Opening ASAR dataset {}', filepath)

    # Open the dataset using a custom reader
    gdal_dataset: gdal.Dataset = reader.get_gdal_dataset(filepath)

    # Extract metadata attributes
    metadata = get_metadata(gdal_dataset)

    # Duplicate, read directly from file, as gdal does not parse some necessary metadata
    metadata["direct_parse"] = envisat_direct.parse_direct(filepath)

    # Create an xarray Dataset with pixel data and metadata attributes
    dataset: xr.Dataset = create_dataset(metadata, filepath)

    return dataset


def create_dataset(metadata: dict[str, Any], filepath: str) -> xr.Dataset:
    number_of_samples = metadata["line_length"]
    product_first_line_utc_time = metadata["first_line_time"]
    product_last_line_utc_time = metadata["last_line_time"]
    print(product_first_line_utc_time)

    number_of_lines = metadata["records"]["main_processing_params"]["num_output_lines"]
    azimuth_time_interval = 1 / metadata["records"]["main_processing_params"]["image_parameters"]["prf_value"][0]
    range_sampling_rate = metadata["records"]["main_processing_params"]["range_samp_rate"]
    image_slant_range_time = metadata["direct_parse"]["slant_time_first"] * 1e-9

    number_of_bursts = 0
    # range_pixel_spacing = scipy.constants.c / (2 * range_sampling_rate)

    attrs = {
        "family_name": "Envisat",
        "number": 1,
        "mode": 1,
        "swaths": metadata["swath"],
        "orbit_number": metadata["abs_orbit"],
        "relative_orbit_number": metadata["rel_orbit"],
        "pass": metadata["pass"],
        "transmitter_receiver_polarisations": metadata["mds1_tx_rx_polar"],
        "product_type": "SLC",
        "start_time": product_first_line_utc_time,
        "stop_time": product_last_line_utc_time,

        "radar_frequency": metadata["records"]["main_processing_params"]["radar_freq"] / 1e9,
        "ascending_node_time": "",
        "azimuth_pixel_spacing": metadata["records"]["main_processing_params"]["azimuth_spacing"],
        "range_pixel_spacing": metadata["records"]["main_processing_params"]["range_samp_rate"],
        "product_first_line_utc_time": product_first_line_utc_time,
        "product_last_line_utc_time": product_last_line_utc_time,
        "azimuth_time_interval": azimuth_time_interval,
        "image_slant_range_time": image_slant_range_time,
        "range_sampling_rate": range_sampling_rate,
        "incidence_angle_mid_swath": metadata["direct_parse"]["incidence_angle_center"],
        "metadata": metadata
    }

    azimuth_time = compute_azimuth_time(
        product_first_line_utc_time, product_last_line_utc_time, number_of_lines
    )

    if number_of_bursts == 0:
        swap_dims = {"line": "azimuth_time", "pixel": "slant_range_time"}
    else:
        raise NotImplementedError(
            "Burst processing is not implemented yet."
        )

    coords = {
        "pixel": np.arange(0, number_of_samples, dtype=int),
        "line": np.arange(0, number_of_lines, dtype=int),
        # set "units" explicitly as CF conventions don't support "nanoseconds".
        # See: https://github.com/pydata/xarray/issues/4183#issuecomment-685200043
        "azimuth_time": (
            "line",
            azimuth_time,
            {},
            {"units": f"microseconds since {azimuth_time[0]}"},
        ),
    }

    if True:  # product_information["projection"] == "Slant Range":
        slant_range_time = np.linspace(
            image_slant_range_time,
            image_slant_range_time + (number_of_samples - 1) / range_sampling_rate,
            number_of_samples,
        )
        coords["slant_range_time"] = ("pixel", slant_range_time)

    data = xr.open_dataarray(filepath, engine='rasterio')
    data.encoding.clear()
    data = data.squeeze("band").drop_vars(["band", "spatial_ref"])
    data = data.rename({"y": "line", "x": "pixel"})
    data = data.assign_coords(coords)
    data = data.swap_dims(swap_dims)

    data.attrs.update(attrs)
    data.encoding.update({})

    return xr.Dataset(attrs=attrs, data_vars={"measurements": data})


def get_chirp_parameters(dataset: gdal.Dataset) -> dict[str, Any]:
    """
    Parse dataset metadata for chirp parameters.

    :param dataset: ASAR dataset.
    :return: dictionary with chirp parameters.
    """
    metadata = dataset.GetMetadata(domain='RECORDS')
    params: dict[str, Any] = dict()
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


def get_chirp_cal_pulse_info(metadata: dict[str, str]) -> list[dict[str, Any]]:
    """
    Parse calibration pulse information from metadata into list of dictionaries.

    :param metadata: Dictionary containing metadata with CAL_PULSE_INFO entries
    :return: List of dictionaries containing calibration pulse parameters
    """
    cal_info_dict: dict[str, Any] = {}

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


def compute_azimuth_time(product_first_line_utc_time: np.datetime64,
                         product_last_line_utc_time: np.datetime64,
                         number_of_lines: int) -> np.ndarray:
    azimuth_time = pd.date_range(start=product_first_line_utc_time, end=product_last_line_utc_time,
                                 periods=number_of_lines)
    return azimuth_time.values

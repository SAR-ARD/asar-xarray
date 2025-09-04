"""ASAR Xarray Dataset Reader."""

import os
from typing import Dict, Any

import pandas as pd
import xarray as xr
import numpy as np
import math
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
    attributes: dict[str, Any] = {}
    process_general_metadata(gdal_dataset, attributes)
    process_records_metadata(gdal_dataset, attributes)
    process_derived_subdatasets_metadata(gdal_dataset, attributes)

    attributes['chirp_parameters'] = get_chirp_parameters(gdal_dataset)

    return attributes


def open_asar_dataset(filename_or_obj: str | os.PathLike[Any] | ReadBuffer[
        Any] | bytes | memoryview | AbstractDataStore,
                      polarization=None) -> xr.Dataset:
    """
    Open an ASAR dataset and converts it into an xarray Dataset.

    This function reads the metadata and pixel data from the given ASAR dataset file,
    processes the metadata into attributes, and constructs an xarray Dataset.

    :param filename_or_obj: The path to the ASAR dataset file. It can be a string,
                     a PathLike object, a ReadBuffer, or an AbstractDataStore.
    :param polarization: AP mode polarization
    :return: An xarray Dataset containing the pixel data and metadata attributes.
    :raises NotImplementedError: If the filepath is not a string.
    """
    if not isinstance(filename_or_obj, str):
        raise NotImplementedError(f'Filepath type {type(filename_or_obj)} is not supported')

    logger.debug('Opening ASAR dataset {}', filename_or_obj)

    # Open the dataset using a custom reader
    gdal_dataset: gdal.Dataset = reader.get_gdal_dataset(filename_or_obj)

    # Extract metadata attributes
    metadata = get_metadata(gdal_dataset)

    product_str = metadata["sph_descriptor"]

    if product_str == "Image Mode SLC Image" or product_str == "AP Mode SLC Image":
        metadata["product_type"] = "SLC"
    elif product_str == "Image Mode Precision Image" or product_str == "AP Mode Precision Image":
        metadata["product_type"] = "GRD"
    else:
        raise RuntimeError(
            "Product \"{}\" not supported, only Image mode files supported(IMS & IMP) supported for now".format(
                product_str))

    pol1 = metadata["mds1_tx_rx_polar"]
    pol2 = metadata["mds2_tx_rx_polar"]
    metadata["polarization_idx"] = 0
    if "AP Mode" in product_str:
        if polarization is None:
            raise RuntimeError("Polarization must be set for AP Mode")

        if polarization == pol1:
            metadata["polarization_idx"] = 0
        elif polarization == pol2:
            metadata["polarization_idx"] = 1
        else:
            raise RuntimeError("Argument polarization is {} - MDS1 = {} MDS2 = {}".format(polarization, pol1, pol2))
    else:
        if polarization is None:
            polarization = pol1
        else:
            if polarization != pol1:
                raise RuntimeError("Argument polarization is {} - MDS1 = {}".format(polarization, pol1))

    metadata["txrx_polarization"] = polarization
    # Duplicate, read directly from file, as gdal does not parse some necessary metadata
    metadata["direct_parse"] = envisat_direct.parse_direct(filename_or_obj, metadata, polarization)

    # Create an xarray Dataset with pixel data and metadata attributes
    dataset: xr.Dataset = create_dataset(metadata, filename_or_obj)

    return dataset


def create_dataset(metadata: dict[str, Any], filepath: str) -> xr.Dataset:
    """
    Create an xarray Dataset from ASAR metadata and file path.

    This function constructs the coordinates, attributes, and data variables
    for an ASAR product, using the provided metadata and file path.

    :param metadata: Dictionary containing ASAR product metadata.
    :param filepath: Path to the ASAR dataset file.
    :param filepath: Path to the ASAR dataset file.
    :param polarization: AP mode polarization
    :return: An xarray Dataset with pixel data, coordinates, and attributes.
    """
    number_of_samples = metadata["line_length"]
    product_first_line_utc_time = metadata["first_line_time"]
    product_last_line_utc_time = metadata["last_line_time"]

    number_of_lines = metadata["records"]["main_processing_params"]["num_output_lines"]
    azimuth_time_interval = metadata["line_time_interval"]

    range_sampling_rate = metadata["records"]["main_processing_params"]["range_samp_rate"]
    image_slant_range_time = metadata["direct_parse"]["slant_time_first"] * 1e-9

    range_pixel_spacing = metadata["records"]["main_processing_params"]["range_spacing"]

    product_str = metadata["sph_descriptor"]

    if product_str == "Image Mode SLC Image" or product_str == "AP Mode SLC Image":
        product_type = "SLC"
    elif product_str == "Image Mode Precision Image" or product_str == "AP Mode Precision Image":
        product_type = "GRD"
    else:
        raise RuntimeError(
            "Product \"{}\" not supported, only Image mode files supported(IMS & IMP) supported for now".format(
                product_str))

    attrs = {
        "family_name": "Envisat",
        "number": 1,
        "mode": 1,
        "swaths": metadata["swath"],
        "orbit_number": metadata["abs_orbit"],
        "relative_orbit_number": metadata["rel_orbit"],
        "pass": metadata["pass"],
        "transmitter_receiver_polarisations": metadata["txrx_polarization"],
        "product_type": metadata["product_type"],
        "start_time": product_first_line_utc_time,
        "stop_time": product_last_line_utc_time,
        "range_pixel_spacing": metadata["range_spacing"],
        "radar_frequency": metadata["records"]["main_processing_params"]["radar_freq"] / 1e9,
        "ascending_node_time": "",
        "product_first_line_utc_time": product_first_line_utc_time,
        "product_last_line_utc_time": product_last_line_utc_time,
        "azimuth_time_interval": azimuth_time_interval,
        "image_slant_range_time": image_slant_range_time,
        "range_sampling_rate": range_sampling_rate,
        "incidence_angle_mid_swath": metadata["direct_parse"]["incidence_angle_center"] * 2 * math.pi / 360,
        "metadata": metadata
    }

    azimuth_time = compute_azimuth_time(
        product_first_line_utc_time, product_last_line_utc_time, number_of_lines
    )

    swap_dims = {"line": "azimuth_time", "pixel": "slant_range_time"}

    coords: dict[str, Any] = {
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

    if product_type == "SLC":
        slant_range_time = np.linspace(
            image_slant_range_time,
            image_slant_range_time + (number_of_samples - 1) / range_sampling_rate,
            number_of_samples,
        )
        coords["slant_range_time"] = ("pixel", slant_range_time)
    else:

        # generate slant range times from ground ranges for ground range products
        # this is easier due to the Envisat only having GRSR metadata unlike Sentinel1
        # however xarray/Sarsen handle GRD conversion differently for S1
        ground_range = np.linspace(
            0,
            range_pixel_spacing * (number_of_samples - 1),
            number_of_samples,
        )

        # numpy polyval expects the polynomial top be highest ranked first
        coeffs = list(reversed(metadata["direct_parse"]["grsr_coeffs"]))

        slant_ranges = np.polyval(coeffs, ground_range)
        slant_ranges *= 2

        c = 299792458
        slant_range_times = slant_ranges / c

        coords["slant_range_time"] = ("pixel", slant_range_times)

    data = xr.open_dataarray(filepath, engine='rasterio')

    if len(data.data) == 1:

        data = data.squeeze("band").drop_vars(["band", "spatial_ref"])
    elif len(data.data) == 2:
        data = xr.DataArray(data=data.data[metadata["polarization_idx"]], dims=["y", "x"])

    data.encoding.clear()
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
    params: dict[str, Any] = {
        'zero_doppler_time': utils.get_envisat_time(metadata.get('CHIRP_PARAMS_ADS_ZERO_DOPPLER_TIME')),
        'attach_flag': bool(int(metadata.get('CHIRP_PARAMS_ADS_ATTACH_FLAG', '0'))),
        'beam_id': metadata.get('CHIRP_PARAMS_ADS_BEAM_ID'), 'polarisation': metadata.get('CHIRP_PARAMS_ADS_POLAR'),
        'chirp': {}}
    # Non-float values
    for key, value in metadata.items():
        if 'CHIRP_PARAMS_ADS_CHIRP' in key:
            new_key = key.replace('CHIRP_PARAMS_ADS_CHIRP_', '').lower()
            params['chirp'][new_key] = float(value)

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


def compute_azimuth_time(
        product_first_line_utc_time: np.datetime64,
        product_last_line_utc_time: np.datetime64,
        number_of_lines: int
) -> np.ndarray:
    """
    Compute an array of azimuth times for each line in the ASAR product.

    This function generates a sequence of evenly spaced time values between the
    first and last line UTC times, corresponding to the number of lines in the product.

    :param product_first_line_utc_time: UTC time of the first line (as np.datetime64).
    :param product_last_line_utc_time: UTC time of the last line (as np.datetime64).
    :param number_of_lines: Total number of lines in the product.
    :return: Numpy array of azimuth times for each line.
    """
    azimuth_time = pd.date_range(
        start=product_first_line_utc_time,
        end=product_last_line_utc_time,
        periods=number_of_lines
    )
    return np.asarray(azimuth_time.values, dtype='datetime64[ns]')

"""Module for parsing Envisat direct access data structures and extracting metadata."""
import struct
from typing import Any
import os
import math
import pathlib
import numpy as np
from asar_xarray import utils
from numpy.typing import NDArray


def parse_int(s: str) -> int:
    """
    Parse an integer value from a string representation of a field.

    Parameters
    ----------
    s String representation of the field, e.g., "FIELD_NAME=<bytes>=value".

    Returns
    -------
    Integer value of the field.
    """
    s = s.replace("<bytes>", "")
    s = s[s.index("=") + 1:]
    # print(s)
    return int(s)


def __calc_distance(latitude: float, longitude: float, altitude: float = 0.0) -> float:
    """
    Calculate the distance from the Earth's center to a point specified by latitude, longitude, and altitude.

    Parameters
    ----------
    latitude Latitude of the point.
    longitude Longitude of the point.
    altitude Altitude of the point above sea level (default is 0.0).

    Returns
    -------
    Distance from the Earth's center to the specified point in meters.
    """
    dtor = math.pi / 180.0
    a = 6378137.0
    b = 6356752.3142451794975639665996337
    flat_earth_coef = 1.0 / ((a - b) / a)
    e2 = 2.0 / flat_earth_coef - 1.0 / (flat_earth_coef * flat_earth_coef)

    lat = latitude * dtor
    lon = longitude * dtor

    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)

    n = (a / math.sqrt(1.0 - e2 * sin_lat * sin_lat))
    ncos_lat = (n + altitude) * cos_lat

    sin_lon = math.sin(lon)
    cos_lon = math.cos(lon)

    x_pos = ncos_lat * cos_lon
    y_pos = ncos_lat * sin_lon
    z_pos = (n + altitude - e2 * n) * sin_lat
    return math.sqrt(x_pos ** 2 + y_pos ** 2 + z_pos ** 2)


class EnvisatADS:
    """Class representing an Envisat Annotation Data Set (ADS) descriptor."""

    def __init__(self, buffer: bytes) -> None:
        """Initialize the ADS descriptor from a buffer of bytes."""
        str_arr = buffer.decode("ascii").split("\n")
        name = str_arr[0].replace("DS_NAME=\"", "").replace("\"", "").strip()
        self.name = name
        self.filename = str_arr[2].replace("FILENAME=\"", "").replace(" \"", "")
        self.num = parse_int(str_arr[5])
        self.size = parse_int(str_arr[4])
        self.offset = parse_int(str_arr[3])

    def __str__(self) -> str:
        """Return a string representation of the ADS descriptor."""
        return "Envisat ADS: \"{}\" {} {} {}".format(self.name, self.offset, self.size, self.num)


def parse_direct(path: str, gdal_metadata: dict[str, Any], polarization: str) -> dict[str, Any]:
    """
    Parse an Envisat product file and extract relevant metadata fields.

    Args:
    ----
        path (str): Path to the Envisat product file.
        polarization (str): Polarization string (e.g., "H/H", "V/V", "H/V", "V/H").

    returns: Dictionary containing extracted metadata fields.
    """
    metadata: dict[str, Any] = {}
    file_buffer = None
    with open(path, "rb") as fp:
        file_buffer = fp.read()

    # read main product header and confirm sph size location
    mph_size = 1247
    mph_str = file_buffer[0:mph_size].decode("ascii")
    assert (mph_str.index("SPH_SIZE") == 1104)
    sph_size = parse_int(mph_str[1104:1104 + 20])

    sph_buf = file_buffer[mph_size:mph_size + sph_size]
    dsd_size = 280
    dsd_num = 18
    dsd_buf = sph_buf[sph_size - dsd_size * dsd_num:]

    antenna_gains, lats, lons, slant_time_first = __process_ads(dsd_buf, dsd_num, dsd_size, file_buffer,
                                                                gdal_metadata, metadata, polarization)

    # antenna gain
    n_samp = gdal_metadata["line_length"]
    spreading_loss: NDArray[Any] = np.array([])
    if gdal_metadata["sample_type"] == "DETECTED":
        gain_arr = np.ones(n_samp)
        spreading_loss = np.ones(n_samp)
    else:
        # antenna gain
        c = 299792458
        range_spacing = c / (2 * gdal_metadata["records"]["main_processing_params"]["range_samp_rate"])
        range_ref = gdal_metadata["records"]["main_processing_params"]["range_ref"]
        r_first = c * slant_time_first * 1e-9 / 2

        osv = gdal_metadata["records"]["main_processing_params"]["orbit_state_vectors"]

        sat_x = osv[0]["x_pos_1"] * 1e-2
        sat_y = osv[0]["y_pos_1"] * 1e-2
        sat_z = osv[0]["z_pos_1"] * 1e-2
        gain_list: list[float] = []
        for n in range(n_samp):
            # https://github.com/senbox-org/microwave-toolbox/blob/master/sar-op-calibration/src/main/java/eu/esa/sar/calibration/gpf/calibrators/ASARCalibrator.java
            r = r_first + n * range_spacing
            geo_interp_idx = (n / n_samp) * (len(lats) - 1)
            idx = int(geo_interp_idx)
            fract = geo_interp_idx % 1
            # interpolate geogrid to match first line geogrid to first OSV
            lat = lats[idx] + (lats[idx + 1] - lats[idx]) * fract
            lon = lons[idx] + (lons[idx + 1] - lons[idx]) * fract

            sar_dis = math.sqrt(sat_x ** 2 + sat_y ** 2 + sat_z ** 2)

            distance = __calc_distance(lat, lon)

            # elevation angle, cosine law from three sides, slant range,
            # earth center to satellite, earth center to target
            angle_cos = (r * r + sar_dis * sar_dis - distance * distance) / (2 * r * sar_dis)
            elev_angle = np.rad2deg(math.acos(angle_cos))

            # find the gain from LUT, with 201 gains against reference elevation angle with 0.05 degree steps
            elev_idx = int((elev_angle - metadata["antenna_ref_elev_angle"]) / 0.05)
            elev_idx += 100
            gain = 1.0
            if 0 <= elev_idx <= len(antenna_gains):
                # dB -> linear
                gain = math.pow(10, antenna_gains[elev_idx] / 10)

            gain_list.append(1 / gain)
        gain_arr = np.array(gain_list)

        # calculate spreading loss compensation

        spread_loss_power = 3.0
        if "APS" in gdal_metadata["product"]:
            spread_loss_power = 4.0
        for n in range(n_samp):
            r = r_first + n * range_spacing
            factor = math.pow((range_ref / r), spread_loss_power)
            spreading_loss = np.append(spreading_loss, 1 / factor)

    factor_offset = gdal_metadata["polarization_idx"]
    cal_factor = gdal_metadata["records"]["main_processing_params"]["calibration_factors"][factor_offset][
        "ext_cal_fact"]

    metadata["cal_factor"] = cal_factor
    metadata["cal_vector"] = np.array(spreading_loss) * np.array(gain_arr)

    return metadata


def __process_ads(dsd_buf: bytes, dsd_num: int, dsd_size: int, file_buffer: bytes,
                  gdal_metadata: dict[str, Any], metadata: dict[Any, Any], polarization: str) -> tuple[
        tuple[float, ...], Any, list[float | Any], float]:
    """
    Process the Annotation Data Sets (ADS) in the Envisat product file.

    Parameters
    ----------
    dsd_buf Buffer containing the ADS descriptors
    dsd_num Number of ADS descriptors
    dsd_size Size of each ADS descriptor
    file_buffer File buffer
    gdal_metadata Metadata extracted using GDAL
    metadata Metadata dictionary to populate
    polarization Polarization string (e.g., "H/H", "V/V", "H/V", "V/H")

    Returns
    -------
    Tuple containing antenna gains, latitudes, longitudes, and the first slant time.
    """
    lats: list[float] = []
    lons: list[float] = []
    slant_time_first = 0.0
    antenna_gains: tuple[float, ...] = (0.0,)
    for i in range(dsd_num):
        ads = EnvisatADS(dsd_buf[i * dsd_size:(i + 1) * dsd_size])
        lats_new, lons_new, slant_time_first_new = __process_geolocation_grid_ads(ads, file_buffer, metadata)
        lats = lats_new if lats_new else lats
        lons = lons_new if lons_new else lons
        slant_time_first = slant_time_first_new if slant_time_first_new else slant_time_first

        antenna_gains_new = __process_cal_ads(ads, gdal_metadata, metadata, polarization)
        antenna_gains = antenna_gains_new if antenna_gains_new else antenna_gains

        process_sr_gr_ads(ads, file_buffer, metadata)
    return antenna_gains, lats, lons, slant_time_first


def __process_geolocation_grid_ads(ads: EnvisatADS, file_buffer: bytes, metadata: dict[Any, Any]) -> tuple[
        Any, list[float | Any], float]:
    """
    Process the Geolocation Grid ADS to extract latitude, longitude, slant time, and incidence angle information.

    Parameters
    ----------
    ads EnvisatADS
    file_buffer File buffer
    metadata Metadata dictionary to populate

    Returns
    -------
    Returns a tuple containing lists of latitudes, longitudes, and the first slant time.
    """
    if ads.name == "GEOLOCATION GRID ADS":
        rec_size = 521
        assert ((ads.size // ads.num) == rec_size)
        geoloc_buf = file_buffer[ads.offset:ads.offset + ads.size]
        middle_idx = ads.num // 2
        geoloc_record = geoloc_buf[middle_idx * rec_size: (middle_idx + 1) * rec_size]
        # Geolocation Grid ADSRs header
        header_size = 12 + 1 + 4 + 4 + 4

        lats_buffer = geoloc_buf[header_size + 11 * 4 * 3: header_size + 11 * 4 * 4]
        lons_buffer = geoloc_buf[header_size + 11 * 4 * 4: header_size + 11 * 4 * 5]

        lats = list(struct.unpack(">11i", lats_buffer))
        lons = list(struct.unpack(">11i", lons_buffer))
        lats = [e * 1e-6 for e in lats]
        lons = [e * 1e-6 for e in lons]

        # tiepoints, 11 of big endian floats for each of the following:
        # samp numbers, slant range times, angles, lats, longs
        block_size = 11 * 4
        slant_time_offset = header_size + 1 * block_size
        incidence_angle_offset = header_size + 2 * block_size
        # adjust to middle of 11
        incidence_angle_offset += 5 * 4

        slant_time_first = struct.unpack(">f", geoloc_record[slant_time_offset:slant_time_offset + 4])[0]
        incidence_angle_middle = \
            struct.unpack(">f", geoloc_record[incidence_angle_offset:incidence_angle_offset + 4])[0]

        metadata["slant_time_first"] = slant_time_first
        metadata["incidence_angle_center"] = incidence_angle_middle
        return lats, lons, slant_time_first
    return [], [], 0.0


def __process_cal_ads(ads: EnvisatADS, gdal_metadata: dict[str, Any], metadata: dict[Any, Any], polarization: str) -> \
        tuple[float, ...]:
    """
    Process the EXTERNAL CALIBRATION ADS to extract antenna gain information.

    Parameters
    ----------
    ads EnvisatADS
    gdal_metadata Metadata extracted using GDAL
    metadata Metadata dictionary to populate
    polarization Polarization string (e.g., "H/H", "V/V", "H/V", "V/H")

    Returns
    -------
    Tuple containing antenna gains.
    """
    antenna_gains = ()

    if gdal_metadata["records"]["main_processing_params"]["ant_elev_corr_flag"]:
        return antenna_gains

    if ads.name == "EXTERNAL CALIBRATION":

        aux_folder = pathlib.Path(os.path.abspath(__file__)).parent
        prod_name = gdal_metadata["product"]
        aux_folder /= "auxiliary"
        if ".N1" in prod_name:
            aux_folder /= "ASAR_Auxiliary_Files"
            aux_folder /= "ASA_XCA_AX"
        elif ".E1" in prod_name:
            aux_folder /= "ERS1"
        elif ".E2" in prod_name:
            aux_folder /= "ERS2"

        for p in os.scandir(aux_folder):
            if ads.filename == p.name:
                with open(p.path, "rb") as fp:
                    ext_cal_buf = fp.read()
                    swath = gdal_metadata["swath"]
                    swath_offset = ord(swath[2]) - ord("1")
                    pol_offset = {"H/H": 0, "V/V": 1, "H/V": 2, "V/H": 3}[polarization]

                # Envisat_Product_Spec_Vol8.pdf
                # 8.6.2 External Calibration Data
                offset = 1247 + 378

                offset += 12
                offset += 4
                offset += 26 * 28 + 4 * 4

                mid_angles = struct.unpack(">7f", ext_cal_buf[offset:offset + 4 * 7])

                offset += 8 * 4

                offset += 804 * 4 * swath_offset
                offset += 201 * 4 * pol_offset

                antenna_gains = struct.unpack(">201f", ext_cal_buf[offset:offset + 4 * 201])
                metadata["antenna_ref_elev_angle"] = mid_angles[swath_offset]
    return antenna_gains


def process_sr_gr_ads(ads: EnvisatADS, file_buffer: bytes, metadata: dict[Any, Any]) -> None:
    """
    Extract SR/GR conversion coefficients from the SR GR ADS.

    Parameters
    ----------
    ads EnvisatADS
    file_buffer File buffer
    metadata Metadata dictionary to populatex

    Returns
    -------
    None
    """
    if ads.name == "SR GR ADS" and ads.size > 0:

        # Envisat file specification says it is SR/GR Conversion ADSR,
        # however the polynomial is for GR to SR...
        srgr_buf = file_buffer[ads.offset:ads.offset + ads.size]
        grsr_coeffs = []
        for i in range(ads.num):
            one_srgr = srgr_buf[i * 55:i * 55 + 41]

            r = struct.unpack(">iiicff5f", one_srgr)

            srgr_el: dict[str, Any] = {}

            mjd_arr = [str(k) for k in r[0:3]]
            mjd_str = ",".join(mjd_arr)

            srgr_el["azimuth_time"] = utils.get_envisat_time(mjd_str)
            srgr_el["slr0"] = r[4]
            srgr_el["gr0"] = r[5]
            srgr_el["grsr_poly_coeffs"] = r[6:]
            grsr_coeffs.append(srgr_el)

        metadata["grsr_coeffs"] = grsr_coeffs

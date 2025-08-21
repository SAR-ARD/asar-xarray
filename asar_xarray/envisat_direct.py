"""Module for parsing Envisat direct access data structures and extracting metadata."""
import struct
from typing import Any
import os
import math
import pathlib


def parse_int(s: str) -> int:
    """Parse an integer value from a string representation of a field."""
    s = s.replace("<bytes>", "")
    s = s[s.index("=") + 1:]
    # print(s)
    return int(s)


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


def parse_direct(path: str, gdal_metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Parse an Envisat product file and extract relevant metadata fields.

    Args:
    ----
        path (str): Path to the Envisat product file.

    returns: Dictionary containing extracted metadata fields.
    """
    metadata: dict[str, Any] = {}
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

    for i in range(dsd_num):
        ads = EnvisatADS(dsd_buf[i * dsd_size:(i + 1) * dsd_size])
        if ads.name == "GEOLOCATION GRID ADS":
            extract_geolocation_metadata(ads, file_buffer, metadata)

        if ads.name == "EXTERNAL CALIBRATION":
            extract_external_calibration_metadata(ads, gdal_metadata, metadata)

        if ads.name == "SR GR ADS" and ads.size > 0:
            srgr_coeffs = extract_srgr_coeffs(ads, file_buffer)
            metadata["srgr_coeffs"] = srgr_coeffs

    # calculate spreading loss compensation
    c = 299792458

    n_samp = gdal_metadata["line_length"]
    range_spacing = c / (2 * gdal_metadata["records"]["main_processing_params"]["range_samp_rate"])
    range_ref = gdal_metadata["records"]["main_processing_params"]["range_ref"]
    r_first = c * metadata["slant_time_first"] * 1e-9 / 2

    spreading_loss = []
    for n in range(n_samp):
        r = r_first + n * range_spacing
        factor = math.sqrt((range_ref / r) ** 3)
        spreading_loss.append(1 / factor)

    cal_factor = gdal_metadata["records"]["main_processing_params"]["calibration_factors"][0]["ext_cal_fact"]

    metadata["cal_factor"] = cal_factor
    metadata["cal_vector"] = spreading_loss

    return metadata


def extract_geolocation_metadata(ads: EnvisatADS, file_buffer: bytes, metadata: dict[str, Any]) -> None:
    """
    Extract geolocation metadata from the GEOLOCATION GRID ADS record.

    Args:
    ----
        ads: EnvisatADS object containing ADS descriptor information.
        file_buffer: The full file buffer as bytes.
        metadata: Dictionary to store extracted metadata.

    Populates the metadata dictionary with:
        - slant_time_first: First slant range time (float).
        - incidence_angle_center: Incidence angle at the center (float).
    """
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


def extract_external_calibration_metadata(ads: EnvisatADS, gdal_metadata: dict[str, Any],
                                          metadata: dict[str, Any]) -> None:
    """
    Extract external calibration metadata from the EXTERNAL CALIBRATION ADS record.

    Args:
    ----
        ads: EnvisatADS object containing ADS descriptor information.
        gdal_metadata: Dictionary with GDAL metadata required for extraction.
        metadata: Dictionary to store extracted metadata.

    Populates the metadata dictionary with:
        - antenna_ref_elev_angle: Reference elevation angle for the antenna (float).
        - antenna_elev_gains: List of antenna elevation gain values (tuple of 201 floats).
    """
    aux_folder = pathlib.Path(os.path.abspath(__file__)).parent
    aux_folder /= "aux"
    aux_folder /= "ASAR_Auxiliary_Files"
    aux_folder /= "ASA_XCA_AX"

    for p in os.scandir(aux_folder):
        if ads.filename == p.name:
            with open(p.path, "rb") as fp:
                ext_cal_buf = fp.read()
                pol = gdal_metadata["mds1_tx_rx_polar"]
                swath = gdal_metadata["swath"]
                swath_offset = ord(swath[2]) - ord("1")
                pol_offset = {"H/H": 0, "V/V": 1, "H/V": 2, "V/H": 3}[pol]

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
                metadata["antenna_elev_gains"] = antenna_gains


def extract_srgr_coeffs(ads: EnvisatADS, file_buffer: bytes) -> list[float]:
    """
    Extract SRGR (Slant Range to Ground Range) coefficients from the SR GR ADS record.

    Args:
    ----
        ads: EnvisatADS object containing ADS descriptor information.
        file_buffer: The full file buffer as bytes.

    Returns: List of SRGR coefficients (list of 5 floats).
    """
    srgr_buf = file_buffer[ads.offset:ads.offset + ads.size]
    r = struct.unpack(">ff5f", srgr_buf[13:41])
    srgr_coeffs = list(r[2:])
    return srgr_coeffs

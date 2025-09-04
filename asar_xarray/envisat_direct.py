"""Module for parsing Envisat direct access data structures and extracting metadata."""
import struct
from typing import Any
import os
import math
import pathlib
import numpy as np


def parse_int(s: str) -> int:
    """Parse an integer value from a string representation of a field."""
    s = s.replace("<bytes>", "")
    s = s[s.index("=") + 1:]
    # print(s)
    return int(s)



def calc_distance(latitude, longitude, altitude=0.0):
    """Lat/Lon to distance from earth center"""
    DTOR = math.pi / 180.0
    RTOD = 180 / math.pi
    A = 6378137.0
    B = 6356752.3142451794975639665996337
    FLAT_EARTH_COEF = 1.0 / ((A - B) / A)
    E2 = 2.0 / FLAT_EARTH_COEF - 1.0 / (FLAT_EARTH_COEF * FLAT_EARTH_COEF)
    EP2 = E2 / (1 - E2)

    lat = latitude * DTOR
    lon = longitude * DTOR

    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)

    N = (A / math.sqrt(1.0 - E2 * sin_lat * sin_lat))
    NcosLat = (N + altitude) * cos_lat

    sin_lon = math.sin(lon)
    cos_lon = math.cos(lon)

    x_pos = NcosLat * cos_lon
    y_pos = NcosLat * sin_lon
    z_pos = (N + altitude - E2 * N) * sin_lat
    return math.sqrt(x_pos**2 + y_pos**2 + z_pos**2)


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


def parse_direct(path: str, gdal_metadata) -> dict[str, Any]:
    """
    Parse an Envisat product file and extract relevant metadata fields.

    Args:
    ----
        path (str): Path to the Envisat product file.

    returns: Dictionary containing extracted metadata fields.
    """
    metadata = {}
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

    for i in range(dsd_num):
        ads = EnvisatADS(dsd_buf[i * dsd_size:(i + 1) * dsd_size])
        #print(ads.name)
        if ads.name == "GEOLOCATION GRID ADS":
            rec_size = 521
            assert ((ads.size // ads.num) == rec_size)
            geoloc_buf = file_buffer[ads.offset:ads.offset + ads.size]
            middle_idx = ads.num // 2
            geoloc_record = geoloc_buf[middle_idx * rec_size: (middle_idx + 1) * rec_size]
            # Geolocation Grid ADSRs header
            header_size = 12 + 1 + 4 + 4 + 4

            lats_buffer = geoloc_buf[header_size + 11 * 4 * 3 : header_size + 11 * 4 * 4]
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



        ext_cal_buf = None
        if ads.name == "EXTERNAL CALIBRATION":

            auxfolder = pathlib.Path(os.path.abspath(__file__)).parent
            prod_name = gdal_metadata["product"]
            auxfolder /= "auxiliary"
            if ".N1" in prod_name:
                auxfolder /= "ASAR_Auxiliary_Files"
                auxfolder /= "ASA_XCA_AX"
            elif ".E1" in prod_name:
                auxfolder /= "ERS1"
            elif ".E2" in prod_name:
                auxfolder /= "ERS2"

            for p in os.scandir(auxfolder):
                if ads.filename == p.name:
                    with open(p.path, "rb") as fp:
                        ext_cal_buf = fp.read()
                        pol = gdal_metadata["mds1_tx_rx_polar"]
                        swath = gdal_metadata["swath"]
                        swath_offset = ord(swath[2]) - ord("1")
                        pol_offset = {"H/H" : 0, "V/V" :1, "H/V" : 2, "V/H":3}[pol]

                        # Envisat_Product_Spec_Vol8.pdf
                        # 8.6.2 External Calibration Data
                        offset = 1247 + 378

                        offset += 12
                        offset += 4
                        offset += 26 * 28 + 4 * 4

                        mid_angles = struct.unpack(">7f", ext_cal_buf[offset:offset+4*7])

                        offset += 8 * 4

                        offset += 804 * 4 * swath_offset
                        offset += 201 * 4 * pol_offset

                        antenna_gains = struct.unpack(">201f", ext_cal_buf[offset:offset + 4 * 201])
                        metadata["antenna_ref_elev_angle"] = mid_angles[swath_offset]

        if ads.name == "SR GR ADS"  and ads.size > 0:
            srgr_buf = file_buffer[ads.offset:ads.offset + ads.size]

            r = struct.unpack(">ff5f", srgr_buf[13:41])


            srgr_coeffs = list(r[2:])
            metadata["srgr_coeffs"] = srgr_coeffs




    

    # antenna gain
    c = 299792458
    n_samp = gdal_metadata["line_length"]
    R_first = c * slant_time_first * 1e-9 / 2
    range_spacing = c / (2 * gdal_metadata["records"]["main_processing_params"]["range_samp_rate"])
    range_ref = gdal_metadata["records"]["main_processing_params"]["range_ref"]
    R_first = c * slant_time_first * 1e-9 / 2

    osv = gdal_metadata["records"]["main_processing_params"]["orbit_state_vectors"]

    sat_x = osv[0]["x_pos_1"] * 1e-2
    sat_y = osv[0]["y_pos_1"] * 1e-2
    sat_z = osv[0]["z_pos_1"] * 1e-2

    gain_arr = []
    for n in range(n_samp):
        # https://github.com/senbox-org/microwave-toolbox/blob/master/sar-op-calibration/src/main/java/eu/esa/sar/calibration/gpf/calibrators/ASARCalibrator.java
        R = R_first + n * range_spacing
        n_geogrid = len(lats)
        geo_interp_idx = (n / n_samp) * (len(lats) - 1)
        idx = int(geo_interp_idx)
        fract = geo_interp_idx % 1
        #interpolate geogrid to match first line geogrid to first OSV
        lat = lats[idx] + (lats[idx+1] - lats[idx]) * fract
        lon = lons[idx] + (lons[idx+1] - lons[idx]) * fract

        sar_dis = math.sqrt(sat_x**2 + sat_y**2 + sat_z**2)

        distance = calc_distance(lat, lon)

        # elevation angle, cosine law from three sides, slant range, earth center to satellite, earth center to target
        angle_cos = (R * R + sar_dis * sar_dis - distance * distance) / (2 * R * sar_dis)
        elev_angle = np.rad2deg(math.acos(angle_cos))

        # find the gain from LUT, with 201 gains against reference elevation angle with 0.05 degree steps
        elev_idx = int((elev_angle - metadata["antenna_ref_elev_angle"]) / 0.05)
        elev_idx += 100
        gain = 1.0
        if elev_idx >= 0 and elev_idx <= len(antenna_gains):
            # dB -> linear
            gain = math.pow(10, antenna_gains[elev_idx] / 10)

        gain_arr.append(gain)






    # calculate spreading loss compensation

    spreading_loss = []
    for n in range(n_samp):
        R = R_first + n * range_spacing
        factor = math.sqrt((range_ref / R) ** 3)
        spreading_loss.append(1/factor)

    cal_factor = gdal_metadata["records"]["main_processing_params"]["calibration_factors"][0]["ext_cal_fact"]

    metadata["cal_factor"] = cal_factor
    metadata["cal_vector"] = np.array(spreading_loss) * np.array(gain_arr)


    return metadata

"""Module for parsing Envisat direct access data structures and extracting metadata."""
import struct
from typing import Any
import os
import math
import pathlib
import numpy as np

from asar_xarray import utils


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
        return "Envisat ADS: \"{}\" offset = {}  sz = {}  num = {}".format(self.name, self.offset, self.size, self.num)



def read_f32(buf, offset):
    return struct.unpack(">f", buf[offset:offset+4])[0]
def read_i32(buf, offset):
    return struct.unpack(">i", buf[offset:offset+4])[0]

def read_mjd(buf, offset):
    return struct.unpack(">iii", buf[offset:offset+12])

def read_mjd_dt(buf, offset):
    mjd = read_mjd(buf, offset)
    return utils.get_envisat_time("{},{},{}".format(mjd[0], mjd[1], mjd[2]))

def parse_wss(path: str, subswath: str) -> dict[str, Any]:



    ss_str = subswath
    ss_idx = ord(subswath[2]) - ord('1')
    fp = open(path, "rb")
    mph = fp.read(1247).decode("ascii")
    mph_arr = mph.split("\n")

    sph_size = 6099
    sph_buf = fp.read(sph_size)

    sph_arr = sph_buf.decode("ascii").split("\n")

    metadata = {}


    metadata["sph_descriptor"] = sph_arr[0].replace("SPH_DESCRIPTOR=", "").replace("\"","").strip()
    metadata["swath"] = ss_str
    metadata["product_type"] = "SLC"


    #TODO
    metadata["txrx_polarization"] = "VV"


    if "PRODUCT=" not in mph_arr[0] or "WSS" not in mph_arr[0]:
        return None, None




    dsd_size = 280
    dsd_num = 18
    dsd_buf = sph_buf[sph_size - dsd_size * dsd_num:]

    data_ds_name = ["MDS1", "MDS2", "MDS3", "MDS4", "MDS5"][ss_idx]

    for i in range(dsd_num):
        ads = EnvisatADS(dsd_buf[i * dsd_size:(i + 1) * dsd_size])

        print(ads.name)

        if ads.name == "MAIN PROCESSING PARAMS ADS":
            mpp_sz = 10069

            assert(ads.size == 5 * mpp_sz)
            fp.seek(ads.offset + ss_idx * 5)
            mpp_buf = fp.read(mpp_sz)


            metadata["range_spacing"] = read_f32(mpp_buf, 44)
            metadata["azimuth_spacing"] = read_f32(mpp_buf, 48)
            metadata["line_time_interval"] = read_f32(mpp_buf, 52)
            metadata["range_samp_rate"] = read_f32(mpp_buf,983)
            metadata["radar_freq"] = read_f32(mpp_buf, 987)

            metadata["records"] = {}
            metadata["records"]["main_processing_params"] = {}
            metadata["records"]["main_processing_params"]["orbit_state_vectors"] = {}

            metadata["direct_parse"] = {"cal_factor":  read_f32(mpp_buf, 1381)}

            osv_arr = []
            osv_offset = 1765
            for i in range(5):
                ts = read_mjd_dt(mpp_buf, osv_offset)
                md = {
                    "state_vect_time_1" : ts,
                    "x_pos_1" : read_i32(mpp_buf, osv_offset+12),
                    "y_pos_1" : read_i32(mpp_buf, osv_offset+16),
                    "z_pos_1": read_i32(mpp_buf, osv_offset +20),
                    "x_vel_1": read_i32(mpp_buf, osv_offset + 24),
                    "y_vel_1": read_i32(mpp_buf, osv_offset + 28),
                    "z_vel_1": read_i32(mpp_buf, osv_offset + 32),
                }
                osv_offset += 12 + 6 * 4
                osv_arr.append(md)

            metadata["records"]["main_processing_params"]["orbit_state_vectors"] = osv_arr



        if ads.name == "GEOLOCATION GRID ADS":

            geogrid_offset = ads.offset + ss_idx * (ads.num / 5) * 521
            fp.seek(int(geogrid_offset))
            geoloc_buf = fp.read(521)

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

            slant_time_first = struct.unpack(">f", geoloc_buf[slant_time_offset:slant_time_offset + 4])[0]
            incidence_angle_middle = \
                struct.unpack(">f", geoloc_buf[incidence_angle_offset:incidence_angle_offset + 4])[0]

            metadata["slant_time_first"] = slant_time_first
            metadata["incidence_angle_center"] = incidence_angle_middle



        if ads.name.strip() == data_ds_name:
            #print(ads)
            fp.seek(ads.offset)
            data_buffer = fp.read(ads.size)
            n_lines = ads.num
            line_sz = int(ads.size / ads.num)

            data_time_arr = []

            for i in range(n_lines):
                mdsr_line = data_buffer[i*line_sz:(i+1)*line_sz]
                header = mdsr_line[0:17]

                mjd = struct.unpack(">iii", header[0:12])
                ts = utils.get_envisat_time("{},{},{}".format(mjd[0], mjd[1], mjd[2]))


                #print(mjd_arr)
                #print(struct.unpack(">i", header[13:]))
                data = mdsr_line[17:]

                # Big endian complex int16 -> complex float32...
                # is there a better way than this?
                data_i16 = np.frombuffer(data, dtype=">i2")
                row_buf = data_i16.astype(np.float32).tobytes()
                data_cf32 = np.frombuffer(row_buf, dtype=np.complex64)
                data_time_arr.append((ts, data_cf32))

            data_time_arr.sort(key = lambda x:x[0])
            cnt = 0
            dup = 0
            prev = 0
            max_idx = 0
            max_val = 0

            final_dat = []
            for i in range(len(data_time_arr) - 1):
                if data_time_arr[i][0] != prev:
                    if i != 0:
                        final_dat.append(data_time_arr[max_idx][1])
                    max_val = np.sum(np.abs(data_time_arr[i][1]))
                    max_idx = i
                    cnt += 1
                else:
                    sum_tmp = np.sum(np.abs(data_time_arr[i][1]))
                    if sum_tmp > max_val:
                        max_idx = i
                        max_val = sum_tmp
                    dup += 1
                prev = data_time_arr[i][0]


            metadata["first_line_time"] = data_time_arr[0][0]
            metadata["last_line_time"] = data_time_arr[-1][0]
            metadata["line_length"] = len(data_time_arr[0][1])
            metadata["num_output_lines"] = len(final_dat)

            #TODO
            metadata["direct_parse"]["cal_vector"] = np.ones(metadata["line_length"])



    print("WSS meta = {}".format(metadata))


    return metadata, final_dat








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
    spreading_loss: np.ndarray[Any] = np.array([])
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
        srgr_buf = file_buffer[ads.offset:ads.offset + ads.size]

        r = struct.unpack(">ff5f", srgr_buf[13:41])

        # Envisat file specification says it is SR/GR Conversion ADSR,
        # however the polynomial is for GR to SR...
        srgr_coeffs = list(r[2:])
        metadata["grsr_coeffs"] = srgr_coeffs

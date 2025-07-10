"""Module for parsing Envisat direct access data structures and extracting metadata."""
import struct
from typing import Any


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
        self.num = parse_int(str_arr[5])
        self.size = parse_int(str_arr[4])
        self.offset = parse_int(str_arr[3])

    def __str__(self) -> str:
        """Return a string representation of the ADS descriptor."""
        return "Envisat ADS: \"{}\" {} {} {}".format(self.name, self.offset, self.size, self.num)


def parse_direct(path: str) -> dict[str, Any]:
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
        if ads.name == "GEOLOCATION GRID ADS":
            rec_size = 521
            assert ((ads.size // ads.num) == rec_size)
            geoloc_buf = file_buffer[ads.offset:ads.offset + ads.size]
            geoloc_buf = file_buffer[ads.offset:ads.offset + ads.size]
            middle_idx = ads.num // 2
            geoloc_record = geoloc_buf[middle_idx * rec_size: (middle_idx + 1) * rec_size]
            # Geolocation Grid ADSRs header
            header_size = 12 + 1 + 4 + 4 + 4
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

        if ads.name == "MAIN PROCESSING PARAMS ADS":

            main_processing_params_buf = file_buffer[ads.offset:ads.offset + ads.size]
            if len(main_processing_params_buf) == 10069:
                sigma_buf = main_processing_params_buf[2029:2029 + 4020]
                gammma_buf = main_processing_params_buf[2029 + 4020:]

                metadata["sigma_calib_vector"] = sigma_buf
                metadata["gamma_calib_vector"] = gammma_buf

    return metadata

from asar_xarray import reader
import pytest


def test___get_gdal_dataset():
    file = 'resources/ASA_IMS_1PNESA20040109_194924_000000182023_00157_09730_0000.N1'
    dataset = reader.get_gdal_dataset(file)
    assert dataset is not None
    assert dataset.GetRasterBand(1).Checksum() != 0

    with pytest.raises(RuntimeError):
        reader.get_gdal_dataset('/non_existent_file')

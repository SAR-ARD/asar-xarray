import os.path

from asar_xarray import asar


def test_open_asar_dataset(resources_dir):
    filepath = os.path.join(resources_dir, 'ASA_IMS_1PNESA20040109_194924_000000182023_00157_09730_0000.N1')
    dataset = asar.open_asar_dataset(filepath)
    assert dataset is not None
    assert dataset.dims['x'] == 5174
    assert dataset.dims['y'] == 30181
    assert dataset.data_vars['pixel_values'].data.shape == (30181, 5174)

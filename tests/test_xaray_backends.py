import xarray as xr


def test_open_dataset():
    file = 'resources/ASA_IMS_1PNESA20040109_194924_000000182023_00157_09730_0000.N1'
    dataset = xr.open_dataset(file, engine='asar')
    assert dataset is not None
    assert dataset.dims['x'] == 5174
    assert dataset.dims['y'] == 30181
    assert dataset.data_vars['pixel_values'].data.shape == (30181, 5174)

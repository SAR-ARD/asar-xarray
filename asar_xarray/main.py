import xarray as xr

if __name__ == "__main__":
    # Example usage
    test_file = ('../tests/resources'
                 '/ASA_IMS_1PNESA20040109_194924_000000182023_00157_09730_0000.N1')
    dataset = xr.open_dataset(test_file, engine='asar')
    # print(dataset)
    print(dataset.attrs)

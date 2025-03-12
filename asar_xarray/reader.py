from osgeo import gdal, ogr

gdal.UseExceptions()


def get_gdal_dataset(filepath: str) -> gdal.Dataset:
    """
    Reads file into gdal dataset.

    :param filepath: File to be read
    :return: Opened dataset
    """

    # dataset: gdal.Dataset = gdal.Open(filepath)
    dataset: gdal.Dataset = gdal.GetDriverByName('ESAT').Open(filepath)
    driver: gdal.Driver = dataset.GetDriver()
    print(driver.GetName())
    print(driver.GetDescription())
    if not dataset:
        raise RuntimeError(f'Could not open file: {filepath}')

    return dataset

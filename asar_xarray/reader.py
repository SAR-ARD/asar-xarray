from osgeo import gdal

gdal.UseExceptions()


def get_gdal_dataset(filepath: str) -> gdal.Dataset:
    """
    Reads file into gdal dataset.

    :param filepath: File to be read
    :return: Opened dataset
    """
    print("Available GDAL drivers:")
    for i in range(gdal.GetDriverCount()):
        driver = gdal.GetDriver(i)
        print(driver.ShortName)

    dataset: gdal.Dataset = gdal.Open(filepath)
    if not dataset:
        raise RuntimeError(f'Could not open file: {filepath}')

    return dataset

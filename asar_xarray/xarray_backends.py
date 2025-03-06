import xarray as xr
from asar_xarray import asar


class AsarBackend(xr.backends.common.BackendEntrypoint):
    """
    Xarray backend of ESR/ASAR satellite data.
    """

    def open_dataset(self, filename_or_obj, *, drop_variables) -> xr.Dataset:
        dataset = asar.open_asar_dataset(filename_or_obj)
        return dataset

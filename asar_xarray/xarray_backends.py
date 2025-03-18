import os
from typing import Any, Iterable

import xarray as xr
from xarray.backends import AbstractDataStore
from xarray.core.types import ReadBuffer

from asar_xarray import asar


class AsarBackend(xr.backends.common.BackendEntrypoint):
    """
    Xarray backend of ESR/ASAR satellite data.
    """

    def open_dataset(self,
                     filename_or_obj: str | os.PathLike[Any] | ReadBuffer[Any] | AbstractDataStore,
                     *,
                     drop_variables: str | Iterable[str] | None = None, ) -> xr.Dataset:
        dataset = asar.open_asar_dataset(filename_or_obj)
        return dataset

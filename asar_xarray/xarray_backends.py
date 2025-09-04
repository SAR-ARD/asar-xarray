"""Asar backend for xarray."""

import os
from typing import Any, Iterable

import xarray as xr
from xarray.backends import AbstractDataStore
from xarray.core.types import ReadBuffer

from asar_xarray import asar


class AsarBackend(xr.backends.common.BackendEntrypoint):
    """Xarray backend of ESR/ASAR satellite data."""

    def open_dataset(self,
                     filename_or_obj: str | os.PathLike[Any] | ReadBuffer[Any] | bytes | memoryview | AbstractDataStore,
                     *,
                     drop_variables: str | Iterable[str] | None = None, polarization=None) -> xr.Dataset:
        """
        Open an ASAR dataset and return it as an xarray Dataset.

        This method uses the ASAR library to open a dataset from the given file or object.
        The dataset is returned as an xarray Dataset, which can be used for further analysis
        or processing.

        :param filename_or_obj: The file path, file-like object, or AbstractDataStore
                                representing the dataset to open.
        :param drop_variables: Optional; a variable or list of variables to exclude
                               from the dataset.
        :param polarization: Optional; specify the polarization to load (e.g., 'HH', 'HV', 'VV', 'VH').
        :return: An xarray Dataset containing the opened ASAR data.
        """
        dataset = asar.open_asar_dataset(filename_or_obj, polarization=polarization)
        return dataset

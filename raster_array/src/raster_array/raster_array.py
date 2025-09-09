from __future__ import annotations

from typing import Any

import numpy as np
import rasterio as rio

from numpy.typing import NDArray, DTypeLike

from raster_array.exceptions import RasterArrayShapeError, RasterArrayDtypeError
from raster_array.raster_metadata import RasterMetadata


class RasterArray:
    """A spatially aware NDArray with raster metadata.

    This class wraps the functionality of numpy.ndarray by adding raster metadata,
    allowing for geospatial operations and interoperability with rasterio.

    Attributes:
        array (NDArray): The underlying numpy array storing the raster data.
        metadata (RasterMetadata): Metadata describing the raster dataset.
    """

    array: NDArray
    metadata: RasterMetadata

    def __init__(self, array: NDArray, metadata: RasterMetadata):
        _validate_3d_array(array)
        _validate_array_shape_matches_metadata_shape(array, metadata)
        _validate_dtype_matches_metadata_dtype(array, metadata)

        self.array = array
        self.metadata = metadata

    # properties ------------------------------------------------------------------
    # methods ---------------------------------------------------------------------
    # static methods --------------------------------------------------------------
    @staticmethod
    def from_raster(
        raster: str | rio.DatasetReader,
        target_nodata: int | float | None = None,
        target_dtype: DTypeLike | None = None,
    ) -> RasterArray:
        if isinstance(raster, rio.DatasetReader):
            return RasterArray._from_datasetreader(raster, target_nodata, target_dtype)

        with rio.open(raster) as src:
            return RasterArray._from_datasetreader(src, target_nodata, target_dtype)

    # magic methods (dunder methods) ----------------------------------------------
    # private helper methods ------------------------------------------------------
    @staticmethod
    def _from_datasetreader(
        src: rio.DatasetReader,
        target_nodata: int | float | None = None,
        target_dtype: DTypeLike | None = None,
    ) -> RasterArray:
        """Core logic for RasterArray.from_raster."""
        src_metadata = RasterMetadata.from_profile(src.profile)

        nodata = target_nodata if target_nodata else src_metadata.nodata
        dtype = target_dtype if target_dtype else src_metadata.dtype

        print(f"src nodata: {src_metadata.nodata}, target nodata: {nodata}")
        print(f"src dtype: {src_metadata.dtype}, target dtype: {dtype}")

        if target_nodata or target_dtype:
            check_valid_nodata(nodata, dtype)

        transform = src_metadata.transform
        src_read_kwargs: dict[str, Any] = {
            "masked": False,
            "out_shape": src_metadata.shape,
            "out_dtype": dtype,
        }

        data = src.read(**src_read_kwargs)
        metadata = src_metadata.copy(
            width=src_read_kwargs["out_shape"][-1],
            height=src_read_kwargs["out_shape"][-2],
            transform=transform,
            nodata=nodata,
            dtype=dtype,
        )

        return RasterArray(data, metadata)


# private helpers --------------------------------------------------------------
def check_valid_nodata(nodata: int | float, dtype: DTypeLike) -> None:
    """Validate nodata value to ensure is logical with dtype.

    The nodata value is always represented by a float in a rasterio.profiles.Profile even if dtype is an integer.
    So if nodata is a float and dtype is an integer, but `is_integer()` called on the ndoata value is True,
    the nodata and dtype combination is still valid.

    Args:
        nodata (int | float): The nodata value for which to check if it is valid with dtype.
        dtype (DTypeLike): The data type for which to check if it is valid with the provided nodata value.

    Raises:
         ValueError: if the nodata value is not valid with the provided dtype of nodata is None
    """
    if nodata is None:
        msg = "nodata cannot be None."
        raise ValueError(msg)

    dtype_kind = np.dtype(dtype).kind
    if dtype_kind in ["i", "u"]:
        # if value is a float but can be converted to an integer, do so here
        if np.issubdtype(type(nodata), np.floating) and nodata.is_integer():  # type: ignore
            nodata = int(nodata)
        if not np.issubdtype(type(nodata), np.integer):
            msg = f"dtype is {np.dtype(dtype).name} and nodata is {str(nodata)} with dtype {np.dtype(type(nodata)).name}."
            raise ValueError(msg)
        if not np.iinfo(dtype).min <= nodata <= np.iinfo(dtype).max:
            msg = f"nodata value of {str(nodata)} is not between the min and max of dtype {np.dtype(dtype).name}"
            raise ValueError(msg)
    elif dtype_kind == "f":
        if not np.isnan(nodata):
            msg = "nodata value should be np.nan for a float dtype."
            raise ValueError(msg)
    else:
        msg = f"dtype must be int and float dtypes, not '{np.dtype(dtype).name}'."
        raise ValueError(msg)


def ensure_valid_nodata(nodata: int | float | None, dtype: DTypeLike) -> int | float:
    if nodata is None:
        msg = "nodata cannot be None."
        raise ValueError(msg)

    dtype_info = (
        np.iinfo(dtype) if np.issubdtype(dtype, np.integer) else np.finfo(dtype)
    )  # type: ignore
    nodata_src_dtype = np.dtype(type(nodata))
    nodata_info = (
        np.iinfo(nodata_src_dtype)
        if np.issubdtype(nodata_src_dtype, np.integer)
        else np.finfo(nodata_src_dtype)
    )  # type: ignore

    is_dtype_integer = np.issubdtype(dtype_info.dtype, np.integer)
    is_nodata_integer = np.issubdtype(nodata_info.dtype, np.integer)

    # if nodata is np.nan and dtype is integer, raise
    if np.isnan(nodata) and is_dtype_integer:
        msg = "nodata value should be an integer for an integer dtype."
        raise ValueError(msg)

    # if nodata is non-coerceable float and dtype is integer, raise
    if is_dtype_integer and (nodata % 1 != 0):
        msg = (
            f"nodata value of {str(nodata)} is not a whole number for an integer dtype."
        )
        raise ValueError(msg)

    # if nodata is out of range for dtype, raise
    if not np.isnan(nodata) and not dtype_info.min <= nodata <= dtype_info.max:
        msg = f"nodata value of {str(nodata)} is not between the min and max of dtype {np.dtype(dtype).name}"
        raise ValueError(msg)

    target_nodata = nodata
    # if nodata is int and dtype float, coerce
    if is_nodata_integer and not is_dtype_integer:
        target_nodata = float(target_nodata)

    # float nodata is coerceable to dtype
    if not is_nodata_integer and is_dtype_integer:
        target_nodata = int(target_nodata)

    return target_nodata


def _validate_3d_array(array: NDArray):
    if array.ndim != 3:
        msg = f"Array must have 3 dimensions, has {array.ndim}"
        raise RasterArrayShapeError(msg)


def _validate_array_shape_matches_metadata_shape(
    array: NDArray, metadata: RasterMetadata
):
    if array.shape != metadata.shape:
        msg = (
            f"Array shape {array.shape} does not match metadata shape {metadata.shape}"
        )
        raise RasterArrayShapeError(msg)


def _validate_dtype_matches_metadata_dtype(array: NDArray, metadata: RasterMetadata):
    if np.dtype(array.dtype).name != np.dtype(metadata.dtype).name:
        msg = (
            f"Array dtype {array.dtype} does not match metadata dtype {metadata.dtype}"
        )
        raise RasterArrayDtypeError(msg)

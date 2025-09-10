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
    @property
    def mask(self) -> NDArray:
        """Return a boolean mask array indicating which pixels are masked.

        Returns:
            NDArray: A boolean array where True indicates a masked pixel. The mask
                is created with the `nodata` value in `RasterArray.metadata.nodata`.
        """
        return (
            np.isnan(self.array)
            if np.isnan(self.metadata.nodata)
            else self.array == self.metadata.nodata
        )

    @property
    def masked(self) -> np.ma.MaskedArray:
        """Return a MaskedArray of the array.


        Returns:
            numpy.ma.MaskedArray: A `MaskedArray` of `RasterArray.array`. The mask
                is created with the `nodata` value in `RasterArray.metadata.nodata`.
        """
        array = np.ma.MaskedArray(
            data=self.array, mask=self.mask, fill_value=self.metadata.nodata
        )

        return array

    # methods ---------------------------------------------------------------------
    def band(self, band_index: int) -> NDArray:
        """Return the given raster band as a 3D numpy array.

        Args:
            band_index (int): the band index, starting at 1 to match rasterio's band index

        Returns:
            NDArray: a 3D array of the given band index.
        """
        return self.array[slice(band_index - 1, band_index), :, :]

    def band_masked(self, band_index: int) -> np.ma.MaskedArray:
        """Return the given raster band as a 3D numpy MaskedArray.

        Args:
            band_index (int): the band index, starting at 1 to match rasterio's band index

        Returns:
            np.ma.MaskedArray: a 3D MaskedArray of the given band index.
        """
        return self.masked[slice(band_index - 1, band_index), :, :]

    def to_raster(self, filename: str) -> None:
        """Save RasterArray as a Cloud Optimized GeoTIFF (COG).

        The output GeoTIFF is a COG, but lacks overviews by default.

        The alpha band is set to "UNSPECIFIED" so that an alpha band is not
        automatically set. Otherwise, 4 band int files are automatically created with RGBA set as the color interpretation,
        which can result in issues with gdal computations when the last band is not actually an alpha band.

        TODO:
            - Handle overviews
            - Handle COG driver properly

        Args:
            filename (str): Path to write the file.
        """
        profile = {**self.metadata.profile, "alpha": "UNSPECIFIED"}

        with rio.open(filename, "w", **write_params) as dst:
            dst.write(self.array)

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

        out_nodata = target_nodata if target_nodata else src_metadata.nodata
        out_dtype = target_dtype if target_dtype else src_metadata.dtype

        if target_nodata or target_dtype:
            out_nodata = ensure_valid_nodata(out_nodata, out_dtype)

        transform = src_metadata.transform
        src_read_kwargs: dict[str, Any] = {
            "masked": False,
            "out_shape": src_metadata.shape,
            "out_dtype": out_dtype,
        }

        data = src.read(**src_read_kwargs)

        # coerce nodata values to out_nodata
        replacement_mask = (
            np.isnan(data)
            if np.isnan(src_metadata.nodata)
            else data == src_metadata.nodata
        )
        data[replacement_mask] = out_nodata

        metadata = src_metadata.copy(
            width=src_read_kwargs["out_shape"][-1],
            height=src_read_kwargs["out_shape"][-2],
            transform=transform,
            nodata=out_nodata,
            dtype=out_dtype,
        )

        return RasterArray(data, metadata)


# private helpers --------------------------------------------------------------
def ensure_valid_nodata(nodata: int | float | None, dtype: DTypeLike) -> int | float:
    """Validate and coerce a nodata value to be compatible with a given numpy dtype.

    This function ensures that the nodata value can be properly used with arrays
    of the specified dtype by performing validation and type coercion when necessary.

    Args:
        nodata (int | float | None): The nodata value to validate. Can be an integer, float, or None.
                For integer dtypes, must be a whole number or coerceable to one.
                For float dtypes, can include np.nan.
        dtype (DTypeLike): The target numpy dtype that the nodata value should be compatible with.
                Can be any numpy dtype or dtype-like object.

    Returns:
        The validated and potentially coerced nodata value as either an int or float:
        - If dtype is integer and nodata is a whole number float, returns int
        - If dtype is float and nodata is an integer, returns float
        - Otherwise returns the original nodata value with appropriate type

    Raises:
        ValueError: If nodata is None
        ValueError: If nodata is np.nan and dtype is an integer type
        ValueError: If nodata is a non-whole number float and dtype is an integer type
        ValueError: If nodata is outside the representable range of the dtype

    Examples:
        >>> ensure_valid_nodata(0, np.int16)
        0
        >>> ensure_valid_nodata(-99.0, np.int16)
        -99
        >>> ensure_valid_nodata(-99, np.float32)
        -99.0
        >>> ensure_valid_nodata(np.nan, np.float32)
        nan
        >>> ensure_valid_nodata(9999, np.uint8)
        ValueError: nodata value of 9999 is not between the min and max of dtype uint8
    """
    if nodata is None:
        msg = "nodata cannot be None."
        raise ValueError(msg)

    dtype_info = (
        np.iinfo(dtype) if np.issubdtype(dtype, np.integer) else np.finfo(dtype)  # type: ignore
    )
    nodata_src_dtype = np.dtype(type(nodata))
    nodata_info = (
        np.iinfo(nodata_src_dtype)  # type: ignore
        if np.issubdtype(nodata_src_dtype, np.integer)
        else np.finfo(nodata_src_dtype)  # type: ignore
    )

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

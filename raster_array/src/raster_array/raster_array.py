import numpy as np

from numpy.typing import NDArray

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
    # magic methods (dunder methods) ----------------------------------------------


# private helpers --------------------------------------------------------------
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

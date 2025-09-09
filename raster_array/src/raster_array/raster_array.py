from numpy.typing import NDArray

from raster_array.exceptions import RasterArrayShapeError
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

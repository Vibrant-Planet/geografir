# type: ignore
"""Tests for the RasterArray class."""

import numpy as np
import pytest
import rasterio as rio


from raster_array.exceptions import RasterArrayShapeError
from raster_array.raster_metadata import RasterMetadata
from raster_array.raster_array import RasterArray


@pytest.fixture(scope="session")
def raster_4_x_4_multiband():
    shape = (2, 4, 4)
    count, height, width = shape
    n = count * height * width
    array = np.arange(0, n).reshape(shape)

    metadata = RasterMetadata(
        crs=rio.CRS.from_epsg(4326),
        count=count,
        width=width,
        height=height,
        dtype=np.int32,
        nodata=-9999,
        transform=rio.transform.Affine(1.0, 0.0, 0.0, 0.0, -1.0, 4.0),
    )

    with rio.io.MemoryFile() as memfile:
        with memfile.open(**metadata.profile) as dataset:
            dataset.write(array)
        with memfile.open() as dataset:
            yield dataset


# test initialization of RasterArray ----------------------------------------------
def test_raster_array_init(raster_4_x_4_multiband):
    array = raster_4_x_4_multiband.read()
    metadata = RasterMetadata.from_profile(raster_4_x_4_multiband.profile)
    raster = RasterArray(array, metadata)

    assert raster.array.shape == (2, 4, 4)
    assert raster.metadata.shape == (2, 4, 4)
    assert raster.metadata.crs == rio.CRS.from_epsg(4326)
    assert raster.metadata.dtype == "int32"
    assert raster.metadata.nodata == -9999
    assert raster.metadata.transform == rio.transform.Affine(
        1.0, 0.0, 0.0, 0.0, -1.0, 4.0
    )


def test_raster_array_shape_error(raster_4_x_4_multiband):
    array = raster_4_x_4_multiband.read()
    metadata = RasterMetadata.from_profile(raster_4_x_4_multiband.profile)

    # clip to 2d
    array = array[0]
    metadata = metadata.copy(count=1)

    with pytest.raises(
        RasterArrayShapeError, match="Array must have 3 dimensions, has 2"
    ):
        RasterArray(array, metadata)

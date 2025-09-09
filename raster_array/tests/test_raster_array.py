# type: ignore
"""Tests for the RasterArray class."""

import numpy as np
import pytest
import rasterio as rio


from raster_array.exceptions import RasterArrayShapeError, RasterArrayDtypeError
from raster_array.raster_metadata import RasterMetadata
from raster_array.raster_array import RasterArray, ensure_valid_nodata


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


# test initialization of RasterArray -------------------------------------------
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

    # clip array 2x3x3 without updating count in metadata
    with pytest.raises(RasterArrayShapeError, match="does not match metadata shape"):
        RasterArray(array[:, :3, :3], metadata)

    # clip to 2d updating metadata
    metadata = metadata.copy(count=1)

    with pytest.raises(
        RasterArrayShapeError, match="Array must have 3 dimensions, has 2"
    ):
        RasterArray(array[0], metadata)


def test_raster_array_dtype_error(raster_4_x_4_multiband):
    array = raster_4_x_4_multiband.read()
    metadata = RasterMetadata.from_profile(raster_4_x_4_multiband.profile)
    metadata = metadata.copy(dtype="int64")

    with pytest.raises(RasterArrayDtypeError, match="does not match metadata dtype"):
        RasterArray(array, metadata)


# test RasterArray.from_raster -------------------------------------------------
def test_from_raster_simple(raster_4_x_4_multiband):
    raster = RasterArray.from_raster(raster_4_x_4_multiband)
    expected_array = raster_4_x_4_multiband.read()

    assert isinstance(raster, RasterArray)
    assert isinstance(raster.metadata, RasterMetadata)
    assert np.array_equal(raster.array, expected_array)


# def test_from_raster_simple_target_dtype(raster_4_x_4_multiband):
#     raster = RasterArray.from_raster(raster_4_x_4_multiband, target_dtype=np.float32)

#     print(raster.array.dtype)
#     print(raster.metadata.dtype)

#     assert isinstance(raster, RasterArray)
#     assert isinstance(raster.metadata, RasterMetadata)
#     assert 0


# test helpers -----------------------------------------------------------------
def test_ensure_valid_nodata():
    # this is an error case
    # print(ensure_valid_nodata(np.nan, np.int16))

    # coerce values if necessary
    assert ensure_valid_nodata(0, np.int16) == 0
    assert ensure_valid_nodata(-99.0, np.int16) == -99
    assert ensure_valid_nodata(1.0, np.float32) == 1.0
    assert ensure_valid_nodata(-99, np.float32) == -99.0
    assert np.isnan(ensure_valid_nodata(np.nan, np.float32))

    # edge cases: should raise errors
    ## None nodata type. There isn't a good way to coerce None to another value.
    with pytest.raises(ValueError, match="nodata cannot be None"):
        ensure_valid_nodata(None, np.int16)
    with pytest.raises(ValueError, match="nodata cannot be None"):
        ensure_valid_nodata(None, np.float32)

    ## nodata is np.nan and dtype is integer
    with pytest.raises(
        ValueError, match="nodata value should be an integer for an integer dtype"
    ):
        ensure_valid_nodata(np.nan, np.int16)

    ## nodata is non-coerceable float and dtype is integer
    with pytest.raises(ValueError, match="is not a whole number for an integer dtype"):
        ensure_valid_nodata(-99.99, np.int16)

    ## nodata is out of range of dtype min, max values
    with pytest.raises(ValueError, match="is not between the min and max of dtype"):
        ensure_valid_nodata(9999, np.uint8)

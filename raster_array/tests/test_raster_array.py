# type: ignore
"""Tests for the RasterArray class."""

import numpy as np
import pytest
import rasterio as rio


from raster_array.exceptions import RasterArrayShapeError, RasterArrayDtypeError
from raster_array.raster_metadata import RasterMetadata
from raster_array.raster_array import RasterArray, ensure_valid_nodata
from raster_array.raster_test_helpers import generate_raster


@pytest.fixture(scope="session")
def raster_4326():
    minx, miny, maxx, maxy = (-120, 36, -119, 37)
    width, height = 10, 10
    transform = rio.transform.from_bounds(minx, miny, maxx, maxy, width, height)

    metadata = RasterMetadata(
        crs=rio.CRS.from_epsg(4326),
        count=1,
        width=width,
        height=height,
        dtype=np.int16,
        nodata=-99,
        transform=transform,
    )
    data = np.arange((width * height), dtype=np.int16).reshape(metadata.shape)

    return RasterArray(data, metadata)


@pytest.fixture(scope="session")
def raster_26910():
    minx, miny, maxx, maxy = (
        790160.7511689162,
        4016578.305503206,
        836981.5460881409,
        4073700.8147444506,
    )
    width, height = 25, 25
    transform = rio.transform.from_bounds(minx, miny, maxx, maxy, width, height)

    metadata = RasterMetadata(
        crs=rio.CRS.from_epsg(26910),
        count=1,
        width=width,
        height=height,
        dtype=np.uint8,
        nodata=0,
        transform=transform,
    )
    data = np.ones(metadata.shape, dtype=np.uint8)

    return RasterArray(data, metadata)


@pytest.fixture(scope="session")
def raster_4_x_4_multiband():
    shape = (2, 4, 4)
    count, height, width = shape
    n = count * height * width
    array = np.arange(0, n, dtype=np.int32).reshape(shape)
    with generate_raster(array, -9999, np.int32) as dataset:
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


# PROPERTIES -------------------------------------------------------------------
# RasterArray.mask -------------------------------------------------------------
def test_raster_array_mask():
    mask = np.array([[[True, False], [False, True]], [[True, False], [False, True]]])

    with generate_raster(
        [[[-99, 1], [1, -99]], [[-99, 1], [1, -99]]], -99, np.int16
    ) as src:
        raster = RasterArray.from_raster(src)
        assert np.array_equal(raster.mask, mask)

    with generate_raster(
        [[[np.nan, 1.0], [1.0, np.nan]], [[np.nan, 1.0], [1.0, np.nan]]],
        np.nan,
        np.float32,
    ) as src:
        raster = RasterArray.from_raster(src)
        assert np.array_equal(raster.mask, mask)


## RasterArray.masked ----------------------------------------------------------
def test_raster_array_masked():
    mask = np.array([[[True, False], [False, True]], [[True, False], [False, True]]])

    data = [[[-99, 1], [1, -99]], [[-99, 1], [1, -99]]]
    with generate_raster(data, -99, np.int16) as src:
        raster = RasterArray.from_raster(src)

        assert isinstance(raster.masked, np.ma.MaskedArray)
        assert np.array_equal(raster.masked.data, data, equal_nan=True)
        assert np.array_equal(raster.masked.mask, mask)
        assert raster.masked.fill_value == -99

    data = [[[np.nan, 1.0], [1.0, np.nan]], [[np.nan, 1.0], [1.0, np.nan]]]
    with generate_raster(
        data,
        np.nan,
        np.float32,
    ) as src:
        raster = RasterArray.from_raster(src)

        assert isinstance(raster.masked, np.ma.MaskedArray)
        assert np.array_equal(raster.masked.data, data, equal_nan=True)
        assert np.array_equal(raster.masked.mask, mask)
        assert np.isnan(raster.masked.fill_value)


# METHODS ----------------------------------------------------------------------
## RasterArray.band ------------------------------------------------------------
def test_raster_array_band(raster_4_x_4_multiband):
    raster = RasterArray.from_raster(raster_4_x_4_multiband)

    assert np.array_equal(raster.band(1), np.arange(0, 16).reshape((1, 4, 4)))
    assert np.array_equal(raster.band(2), np.arange(16, 32).reshape((1, 4, 4)))


## RasterArray.band_masked -----------------------------------------------------
def test_raster_array_band_masked():
    data = [[[-99, 1], [1, -99]], [[-99, 1], [1, -99]]]
    with generate_raster(data, -99, np.int16) as src:
        raster = RasterArray.from_raster(src)
        band_1 = raster.band_masked(1)
        band_2 = raster.band_masked(2)

        assert isinstance(band_1, np.ma.MaskedArray)
        assert np.array_equal(band_1.data, [[[-99, 1], [1, -99]]], equal_nan=True)
        assert np.array_equal(band_1.mask, [[[True, False], [False, True]]])
        assert band_1.fill_value == -99

        assert isinstance(band_2, np.ma.MaskedArray)
        assert np.array_equal(band_2.data, [[[-99, 1], [1, -99]]], equal_nan=True)
        assert np.array_equal(band_2.mask, [[[True, False], [False, True]]])
        assert band_2.fill_value == -99


## RasterArray.conform_to ------------------------------------------------------
def test_raster_array_conform_to_simple():
    src_data = np.arange(1, 17).reshape((1, 4, 4)).astype(np.int16)
    ref_data = np.ones((1, 2, 2), dtype=np.uint8)
    with (
        generate_raster(src_data, nodata=0, dtype=np.int16) as src,
        generate_raster(ref_data, nodata=0, dtype=np.uint8) as ref,
    ):
        src_raster = RasterArray.from_raster(src)
        ref_raster = RasterArray.from_raster(ref)

    conformed = src_raster.conform_to(ref_raster)

    expected_array = np.array([[[9, 10], [13, 14]]])

    assert np.array_equal(conformed.array, expected_array)
    assert conformed.metadata.shape == ref_raster.metadata.shape
    assert conformed.metadata.crs.equals(ref_raster.metadata.crs)
    # nodata and dtype are the same as the input raster
    assert conformed.metadata.nodata == src_raster.metadata.nodata
    assert conformed.metadata.dtype == src_raster.metadata.dtype


def test_raster_array_conform_to_with_src_mask():
    src_data = np.array(
        [
            [
                [0, 1, 1, 0],
                [0, 1, 1, 0],
                [0, 1, 1, 0],
                [0, 1, 1, 0],
            ]
        ],
        dtype=np.int16,
    )
    ref_data = np.ones((1, 2, 4), dtype=np.uint8)

    with (
        generate_raster(src_data, nodata=0, dtype=np.int16) as src,
        generate_raster(ref_data, nodata=0, dtype=np.uint8) as ref,
    ):
        src_raster = RasterArray.from_raster(src)
        ref_raster = RasterArray.from_raster(ref)

    conformed = src_raster.conform_to(ref_raster)

    expected_array = np.array([[[0, 1, 1, 0], [0, 1, 1, 0]]])
    expected_mask = np.array([[[True, False, False, True], [True, False, False, True]]])

    assert np.array_equal(conformed.array, expected_array)
    assert np.array_equal(conformed.mask, expected_mask)
    assert conformed.metadata.shape == ref_raster.metadata.shape
    assert conformed.metadata.crs.equals(ref_raster.metadata.crs)
    # nodata and dtype are the same as the input raster
    assert conformed.metadata.nodata == src_raster.metadata.nodata
    assert conformed.metadata.dtype == src_raster.metadata.dtype


def test_raster_array_conform_to_with_ref_mask():
    src_data = np.full((1, 4, 4), 99, dtype=np.int16)
    ref_data = np.array(
        [
            [
                [0, 0, 0, 0],
                [0, 1, 1, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0],
            ]
        ],
        dtype=np.uint8,
    )
    with (
        generate_raster(src_data, nodata=0, dtype=np.int16) as src,
        generate_raster(ref_data, nodata=0, dtype=np.uint8) as ref,
    ):
        src_raster = RasterArray.from_raster(src)
        ref_raster = RasterArray.from_raster(ref)

    conformed = src_raster.conform_to(ref_raster)

    expected_array = np.array(
        [[[0, 0, 0, 0], [0, 99, 99, 0], [0, 99, 99, 0], [0, 0, 0, 0]]]
    )
    expected_mask = expected_array == 0

    assert np.array_equal(conformed.array, expected_array)
    assert np.array_equal(conformed.mask, expected_mask)
    assert conformed.metadata.shape == ref_raster.metadata.shape
    assert conformed.metadata.crs.equals(ref_raster.metadata.crs)
    # nodata and dtype are the same as the input raster
    assert conformed.metadata.nodata == src_raster.metadata.nodata
    assert conformed.metadata.dtype == src_raster.metadata.dtype


def test_raster_array_conform_to_with_both_masked():
    src_data = np.array(
        [
            [
                [0, 99, 99, 99],
                [0, 99, 99, 99],
                [0, 99, 99, 99],
                [0, 0, 0, 0],
            ]
        ],
        dtype=np.int16,
    )
    ref_data = np.array(
        [
            [
                [0, 0, 0, 0],
                [1, 1, 1, 0],
                [1, 1, 1, 0],
                [1, 1, 1, 0],
            ]
        ],
        dtype=np.uint8,
    )
    with (
        generate_raster(src_data, nodata=0, dtype=np.int16) as src,
        generate_raster(ref_data, nodata=0, dtype=np.uint8) as ref,
    ):
        src_raster = RasterArray.from_raster(src)
        ref_raster = RasterArray.from_raster(ref)

    conformed = src_raster.conform_to(ref_raster)

    expected_array = np.array(
        [[[0, 0, 0, 0], [0, 99, 99, 0], [0, 99, 99, 0], [0, 0, 0, 0]]]
    )
    expected_mask = expected_array == 0

    assert np.array_equal(conformed.array, expected_array)
    assert np.array_equal(conformed.mask, expected_mask)
    assert conformed.metadata.shape == ref_raster.metadata.shape
    assert conformed.metadata.crs.equals(ref_raster.metadata.crs)
    # nodata and dtype are the same as the input raster
    assert conformed.metadata.nodata == src_raster.metadata.nodata
    assert conformed.metadata.dtype == src_raster.metadata.dtype


def test_raster_array_conform_to_multiband():
    src_data = np.full((2, 4, 4), 99, dtype=np.int16)
    ref_data = np.array(
        [
            [
                [0, 0, 0, 0],
                [0, 1, 1, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0],
            ]
        ],
        dtype=np.uint8,
    )
    with (
        generate_raster(src_data, nodata=0, dtype=np.int16) as src,
        generate_raster(ref_data, nodata=0, dtype=np.uint8) as ref,
    ):
        src_raster = RasterArray.from_raster(src)
        ref_raster = RasterArray.from_raster(ref)

    conformed = src_raster.conform_to(ref_raster)

    expected_array = np.array(
        [[[0, 0, 0, 0], [0, 99, 99, 0], [0, 99, 99, 0], [0, 0, 0, 0]]]
    )
    expected_array = np.stack([expected_array[0]] * 2, axis=0)
    expected_mask = expected_array == 0

    assert np.array_equal(conformed.array, expected_array)
    assert np.array_equal(conformed.mask, expected_mask)
    assert conformed.metadata.shape == (2, 4, 4)
    assert conformed.metadata.crs.equals(ref_raster.metadata.crs)
    # nodata and dtype are the same as the input raster
    assert conformed.metadata.nodata == src_raster.metadata.nodata
    assert conformed.metadata.dtype == src_raster.metadata.dtype


def test_raster_array_conform_to_multiband_w_different_masks():
    src_data = np.array(
        [
            [[99, 0], [0, 0]],
            [[0, 99], [99, 0]],
            [[0, 0], [0, 99]],
            [[0, 0], [0, 0]],
        ],
        dtype=np.int16,
    )
    ref_data = np.array(
        [
            [
                [1, 0],
                [0, 1],
            ]
        ],
        dtype=np.uint8,
    )
    with (
        generate_raster(src_data, nodata=0, dtype=np.int16) as src,
        generate_raster(ref_data, nodata=0, dtype=np.uint8) as ref,
    ):
        src_raster = RasterArray.from_raster(src)
        ref_raster = RasterArray.from_raster(ref)

    conformed = src_raster.conform_to(ref_raster)

    expected_array = np.array(
        [
            [[99, 0], [0, 0]],
            [[0, 0], [0, 0]],
            [[0, 0], [0, 99]],
            [[0, 0], [0, 0]],
        ],
        dtype=np.int16,
    )
    expected_mask = expected_array == 0

    assert np.array_equal(conformed.array, expected_array)
    assert np.array_equal(conformed.mask, expected_mask)
    assert conformed.metadata.shape == (4, 2, 2)
    assert conformed.metadata.crs.equals(ref_raster.metadata.crs)
    # nodata and dtype are the same as the input raster
    assert conformed.metadata.nodata == src_raster.metadata.nodata
    assert conformed.metadata.dtype == src_raster.metadata.dtype


def test_raster_array_conform_to_reprojects_resamples(raster_4326, raster_26910):
    src_raster = raster_4326
    ref_raster = raster_26910

    conformed = src_raster.conform_to(ref_raster)

    assert isinstance(conformed, RasterArray)
    # conformed data is from the center of the src raster
    assert conformed.array.min() > 20
    assert conformed.array.max() < 80
    assert conformed.metadata.crs.equals(ref_raster.metadata.crs)
    assert conformed.metadata.width == ref_raster.metadata.width
    assert conformed.metadata.height == ref_raster.metadata.height


def test_raster_array_conform_to_override_nodata():
    src_data = np.array([[[1, 0], [0, 1]]], dtype=np.int16)
    ref_data = np.ones((1, 2, 2), dtype=np.uint8)
    with (
        generate_raster(src_data, nodata=0, dtype=np.int16) as src,
        generate_raster(ref_data, nodata=0, dtype=np.uint8) as ref,
    ):
        src_raster = RasterArray.from_raster(src)
        ref_raster = RasterArray.from_raster(ref)

    conformed = src_raster.conform_to(ref_raster, target_nodata=-99)

    assert conformed.metadata.nodata == -99
    assert np.array_equal(conformed.array, np.array([[[1, -99], [-99, 1]]]))
    assert np.array_equal(conformed.mask, (src_data == 0))


def test_raster_array_conform_to_override_dtype():
    src_data = np.array([[[1, 0], [0, 1]]], dtype=np.int16)
    ref_data = np.ones((1, 2, 2), dtype=np.uint8)
    with (
        generate_raster(src_data, nodata=0, dtype=np.int16) as src,
        generate_raster(ref_data, nodata=0, dtype=np.uint8) as ref,
    ):
        src_raster = RasterArray.from_raster(src)
        ref_raster = RasterArray.from_raster(ref)

    conformed = src_raster.conform_to(ref_raster, target_dtype=np.float32)

    assert conformed.metadata.dtype == np.float32
    assert conformed.array.dtype == np.float32
    assert np.array_equal(
        conformed.array, np.array([[[1.0, 0.0], [0.0, 1.0]]], dtype=np.float32)
    )
    assert np.array_equal(conformed.mask, (src_data == 0))


## RasterArray.to_raster -------------------------------------------------------
def test_raster_array_to_raster(raster_4_x_4_multiband, tmp_path):
    raster = RasterArray.from_raster(raster_4_x_4_multiband)
    out_path = tmp_path / "test.tiff"
    raster.to_raster(out_path)

    reread_raster = RasterArray.from_raster(out_path)

    assert np.array_equal(raster.array, reread_raster.array)


# STATICMETHODS ----------------------------------------------------------------
## RasterArray.from_raster -----------------------------------------------------
type_and_nodata_coercion_data = [
    # (data, src_nodata, target_nodata, src_dtype, target_dtype)
    ([[[0.0, 1.0], [1.0, 0.0]]], 0, -99, np.float32, np.int16),
    ([[[0.0, 1.0], [1.0, 0.0]]], 0, 0, np.float32, np.int16),
    ([[[0.0, 1.0], [1.0, 0.0]]], 0, 0, np.int16, np.float32),
    ([[[0.0, 1.0], [1.0, 0.0]]], 0, np.nan, np.float32, np.float32),
    ([[[np.nan, 1.0], [1.0, np.nan]]], np.nan, -99, np.float32, np.float32),
]


@pytest.mark.parametrize(
    "data, src_nodata, target_nodata, src_dtype, target_dtype",
    type_and_nodata_coercion_data,
)
def test_from_raster_simple_target_nodata_or_dtype_coercion(
    data, src_nodata, target_nodata, src_dtype, target_dtype
):
    array = np.array(data, dtype=src_dtype)
    expected_array = array.astype(target_dtype, copy=True)
    replacement_mask = (
        np.isnan(expected_array)
        if np.isnan(src_nodata)
        else expected_array == src_nodata
    )
    expected_array[replacement_mask] = target_nodata

    with generate_raster(data, src_nodata, src_dtype) as src:
        raster = RasterArray.from_raster(
            src, target_nodata=target_nodata, target_dtype=target_dtype
        )

        assert np.array_equal(raster.array, expected_array, equal_nan=True)
        assert raster.array.dtype == target_dtype
        assert raster.metadata.dtype == target_dtype
        if np.isnan(target_nodata):
            assert np.isnan(raster.metadata.nodata)
        else:
            assert raster.metadata.nodata == target_nodata


def test_from_raster_band_index(raster_4_x_4_multiband):
    all_bands = RasterArray.from_raster(raster_4_x_4_multiband, band_index=None)
    band_1 = RasterArray.from_raster(raster_4_x_4_multiband, band_index=1)
    band_2 = RasterArray.from_raster(raster_4_x_4_multiband, band_index=2)

    assert np.array_equal(all_bands.array[0:1, :, :], band_1.array)
    assert np.array_equal(all_bands.array[1:2, :, :], band_2.array)
    assert all_bands.metadata.count == 2
    assert band_1.metadata.count == 1
    assert band_2.metadata.count == 1


# test helper methods ----------------------------------------------------------
def test_ensure_valid_nodata():
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

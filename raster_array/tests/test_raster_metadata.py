# type: ignore
"""
Tests for the RasterMetadata class.
"""

import numpy as np
import pytest
import rasterio as rio
from rasterio.enums import Compression

from raster_array.raster_metadata import RasterMetadata, NO_RESOLUTION_SPECIFIED
from raster_array.raster_test_helpers import generate_raster


def test_raster_metadata_init_basic():
    """Test basic initialization of RasterMetadata with all parameters."""
    crs = rio.CRS.from_epsg(4326)
    count = 3
    width = 100
    height = 200
    dtype = np.float32
    nodata = -9999.0
    transform = rio.transform.from_bounds(0, 0, 10, 20, width, height)
    resolution = 0.1

    metadata = RasterMetadata(
        crs=crs,
        count=count,
        width=width,
        height=height,
        dtype=dtype,
        nodata=nodata,
        transform=transform,
        resolution=resolution,
    )

    assert metadata.count == count
    assert metadata.crs == crs
    assert metadata.dtype == dtype
    assert metadata.height == height
    assert metadata.nodata == nodata
    assert metadata.resolution == resolution
    assert metadata.transform == transform
    assert metadata.width == width


def test_raster_metadata_init_default_resolution():
    """Test initialization with default resolution parameter."""
    crs = rio.CRS.from_epsg(4326)
    transform = rio.transform.from_bounds(0, 0, 10, 10, 100, 100)

    metadata = RasterMetadata(
        crs=crs,
        count=1,
        width=100,
        height=100,
        dtype=np.uint8,
        nodata=255,
        transform=transform,
        # resolution not provided, should use default
    )

    assert metadata.resolution == NO_RESOLUTION_SPECIFIED


def test_raster_metadata_init_different_dtypes():
    """Test initialization with various numpy dtypes."""
    crs = rio.CRS.from_epsg(4326)
    transform = rio.transform.from_bounds(0, 0, 1, 1, 10, 10)

    dtypes_to_test = [
        np.uint8,
        np.int16,
        np.uint16,
        np.int32,
        np.uint32,
        np.float32,
        np.float64,
        "uint8",
        "float32",
    ]

    for dtype in dtypes_to_test:
        metadata = RasterMetadata(
            crs=crs,
            count=1,
            width=10,
            height=10,
            dtype=dtype,
            nodata=0,
            transform=transform,
        )
        assert metadata.dtype == dtype


def test_raster_metadata_init_different_nodata_types():
    """Test initialization with different nodata value types."""
    crs = rio.CRS.from_epsg(4326)
    transform = rio.transform.from_bounds(0, 0, 1, 1, 10, 10)

    # Integer nodata
    metadata_int = RasterMetadata(
        crs=crs,
        count=1,
        width=10,
        height=10,
        dtype=np.int16,
        nodata=-32768,
        transform=transform,
    )
    assert metadata_int.nodata == -32768
    assert isinstance(metadata_int.nodata, int)

    # Float nodata
    metadata_float = RasterMetadata(
        crs=crs,
        count=1,
        width=10,
        height=10,
        dtype=np.float32,
        nodata=-9999.5,
        transform=transform,
    )
    assert metadata_float.nodata == -9999.5
    assert isinstance(metadata_float.nodata, float)


def test_raster_metadata_init_various_transforms():
    """Test initialization with different types of transform.Affine transforms."""
    crs = rio.CRS.from_epsg(4326)

    # Transform from bounds
    transform_bounds = rio.transform.from_bounds(-180, -90, 180, 90, 360, 180)
    metadata_bounds = RasterMetadata(
        crs=crs,
        count=1,
        width=360,
        height=180,
        dtype=np.float32,
        nodata=-9999,
        transform=transform_bounds,
    )
    assert isinstance(metadata_bounds.transform, rio.transform.Affine)

    # Manual transform.Affine transform
    transform_manual = rio.transform.Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0)
    metadata_manual = RasterMetadata(
        crs=crs,
        count=1,
        width=10,
        height=10,
        dtype=np.float32,
        nodata=-9999,
        transform=transform_manual,
    )
    assert metadata_manual.transform == rio.transform.Affine(
        1.0, 0.0, 0.0, 0.0, -1.0, 10.0
    )


# @property tests -----------------------------------------------------------------
bounds_params = [
    (
        10,
        10,
        rio.transform.Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0),
        (0.0, 0.0, 10.0, 10.0),
    ),
    (
        5,
        5,
        rio.transform.Affine(8.0, 0.0, -20.0, 0.0, -8.0, 20.0),
        (-20.0, -20.0, 20.0, 20.0),
    ),
    (
        2,
        2,
        rio.transform.Affine(4.0, 0.0, 4.0, 0.0, -4.0, 12.0),
        (4.0, 4.0, 12.0, 12.0),
    ),
    (
        11,
        11,
        rio.transform.Affine(3.0, 0.0, -3.0, 0.0, -3.0, 36.0),
        (-3.0, 3.0, 30.0, 36.0),
    ),
]


@pytest.mark.parametrize("width, height, transform, bounds", bounds_params)
def test_raster_metadata_bounds(width, height, transform, bounds):
    metadata = RasterMetadata(
        crs=rio.CRS.from_epsg(4326),
        count=1,
        width=width,
        height=height,
        dtype=np.float32,
        nodata=-9999,
        transform=transform,
    )

    assert metadata.bounds == bounds


def test_raster_metadata_profile():
    metadata = RasterMetadata(
        crs=rio.CRS.from_epsg(4326),
        count=1,
        width=10,
        height=10,
        dtype=np.float32,
        nodata=-9999,
        transform=rio.transform.Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0),
    )
    assert metadata.profile["driver"] == "GTiff"
    assert metadata.profile["bigtiff"] == "YES"
    assert metadata.profile["blockxsize"] == 512
    assert metadata.profile["blockysize"] == 512
    assert metadata.profile["interleave"] == "pixel"
    assert metadata.profile["compress"] == Compression.deflate
    assert metadata.profile["zlevel"] == 9
    assert metadata.profile["tiled"]


def test_raster_metadata_shape():
    metadata = RasterMetadata(
        crs=rio.CRS.from_epsg(4326),
        count=1,
        width=10,
        height=10,
        dtype=np.float32,
        nodata=-9999,
        transform=rio.transform.Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0),
    )
    assert metadata.shape == (1, 10, 10)


# @staticmethods tests -----------------------------------------------------------------
def test_raster_metadata_from_profile():
    profile = rio.profiles.Profile(
        {
            "driver": "GTiff",
            "interleave": "pixel",
            "tiled": True,
            "blockxsize": 512,
            "blockysize": 512,
            "nodata": 0,
            "compress": Compression.deflate,
            "crs": rio.CRS.from_epsg(3310),
            "width": 1859,
            "height": 1566,
            "transform": rio.transform.Affine(5.0, 0.0, -47045.0, 0.0, -5.0, 142190.0),
            "count": 2,
            "dtype": np.uint8,
            "zlevel": 9,
            "bigtiff": "YES",
        }
    )
    metadata = RasterMetadata.from_profile(profile)

    assert profile == metadata.profile


def test_raster_metadata_from_raster():
    with generate_raster([[[0, 1], [1, 0]]], 0, np.int16) as src:
        metadata = RasterMetadata.from_raster(src)

        assert metadata.crs.equals(rio.CRS.from_epsg(4326))
        assert metadata.transform == rio.transform.Affine(1.0, 0.0, 0.0, 0.0, -1.0, 2.0)
        assert metadata.count == 1
        assert metadata.width == 2
        assert metadata.height == 2


# Methods tests -----------------------------------------------------------------
def test_raster_metadata_copy():
    metadata = RasterMetadata(
        crs=rio.CRS.from_epsg(5070),
        count=3,
        width=3,
        height=3,
        dtype="float32",
        nodata=0.0,
        transform=rio.transform.Affine(5.0, 0.0, 0.0, 0.0, -5.0, 5.0),
        resolution=5,
    )
    new_metadata = metadata.copy(nodata=-9999, count=4, band_tags={})

    assert new_metadata.nodata == -9999
    assert new_metadata.count == 4

    all_parameters_changed_metadata = metadata.copy(
        crs=rio.CRS.from_epsg(5070),
        count=2,
        width=5,
        height=9,
        dtype="int32",
        nodata=99,
        transform=rio.transform.Affine(15.0, 10.0, -10.0, 0.0, -15.0, 80.0),
        resolution=10,
    )

    assert all_parameters_changed_metadata.crs == rio.CRS.from_epsg(5070)
    assert all_parameters_changed_metadata.count == 2
    assert all_parameters_changed_metadata.width == 5
    assert all_parameters_changed_metadata.height == 9
    assert all_parameters_changed_metadata.dtype == "int32"
    assert all_parameters_changed_metadata.transform == rio.transform.Affine(
        15.0, 10.0, -10.0, 0.0, -15.0, 80.0
    )
    assert all_parameters_changed_metadata.resolution == 10


# Magic methods (dunder methods) tests --------------------------------------------
def test_raster_metadata_repr():
    metadata = RasterMetadata(
        crs=rio.CRS.from_epsg(4326),
        count=1,
        width=10,
        height=10,
        dtype=np.float32,
        nodata=-9999,
        transform=rio.transform.Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0),
    )
    assert (
        repr(metadata)
        == "RasterMetadata(crs=EPSG:4326, count=1, width=10, height=10, dtype=<class 'numpy.float32'>, nodata=-9999, transform=Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0), resolution=0)"
    )

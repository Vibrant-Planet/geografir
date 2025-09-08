"""
Tests for the RasterMetadata class.
"""

import numpy as np
from rasterio import CRS
from rasterio.transform import from_bounds, Affine

from raster_array.raster_metadata import RasterMetadata, NO_RESOLUTION_SPECIFIED


def test_raster_metadata_init_basic():
    """Test basic initialization of RasterMetadata with all parameters."""
    crs = CRS.from_epsg(4326)
    count = 3
    width = 100
    height = 200
    dtype = np.float32
    nodata = -9999.0
    transform = from_bounds(0, 0, 10, 20, width, height)
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

    assert metadata.crs == crs
    assert metadata.count == count
    assert metadata.width == width
    assert metadata.height == height
    assert metadata.dtype == dtype
    assert metadata.nodata == nodata
    assert metadata.transform == transform
    assert metadata.resolution == resolution


def test_raster_metadata_init_default_resolution():
    """Test initialization with default resolution parameter."""
    crs = CRS.from_epsg(4326)
    transform = from_bounds(0, 0, 10, 10, 100, 100)

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
    crs = CRS.from_epsg(4326)
    transform = from_bounds(0, 0, 1, 1, 10, 10)

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
    crs = CRS.from_epsg(4326)
    transform = from_bounds(0, 0, 1, 1, 10, 10)

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
    """Test initialization with different types of affine transforms."""
    crs = CRS.from_epsg(4326)

    # Transform from bounds
    transform_bounds = from_bounds(-180, -90, 180, 90, 360, 180)
    metadata_bounds = RasterMetadata(
        crs=crs,
        count=1,
        width=360,
        height=180,
        dtype=np.float32,
        nodata=-9999,
        transform=transform_bounds,
    )
    assert isinstance(metadata_bounds.transform, Affine)

    # Manual affine transform
    transform_manual = Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0)
    metadata_manual = RasterMetadata(
        crs=crs,
        count=1,
        width=10,
        height=10,
        dtype=np.float32,
        nodata=-9999,
        transform=transform_manual,
    )
    assert metadata_manual.transform == transform_manual


# Magic methods (dunder methods) tests --------------------------------------------
def test_raster_metadata_repr():
    metadata = RasterMetadata(
        crs=CRS.from_epsg(4326),
        count=1,
        width=10,
        height=10,
        dtype=np.float32,
        nodata=-9999,
        transform=Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0),
    )
    assert (
        repr(metadata)
        == "RasterMetadata(crs=EPSG:4326, count=1, width=10, height=10, dtype=<class 'numpy.float32'>, nodata=-9999, transform=Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0), resolution=0)"
    )

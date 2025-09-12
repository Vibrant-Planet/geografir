"""Raster image profile configurations for COG and GeoTIFF formats.

This module provides standardized profile configurations for creating optimized
raster images in Cloud Optimized GeoTIFF (COG) and standard GeoTIFF formats.
It includes sensible defaults for compression, tiling, and other parameters
that ensure good performance and compatibility.

The profiles are designed to work with rasterio for creating web-optimized
geospatial raster data that can be efficiently served and processed in
cloud environments.

Classes:
    CogProfile: Profile configuration optimized for Cloud Optimized GeoTIFF
        format with COG driver and appropriate compression settings.
    GeoTiffProfile: Profile configuration for standard GeoTIFF format with
        tiling and compression optimizations for general use.

Functions:
    apply_cog_profile: Apply COG-specific profile settings to an existing
        raster profile, removing incompatible parameters.
    apply_geotiff_profile: Apply GeoTIFF profile settings to an existing
        raster profile with standard optimization parameters.

Constants:
    DEFAULT_BLOCK_SIZE (int): Default tile/block size in pixels (512).
    DEFAULT_COMPRESS_Z_LEVEL (int): Default compression level for deflate (9).
    DEFAULT_DRIVER_COG (str): Driver name for COG format ("COG").
    DEFAULT_DRIVER_GTIFF (str): Driver name for GeoTIFF format ("GTiff").
    DEFAULT_INTERLEAVE (str): Default pixel interleaving method ("pixel").
    DEFAULT_TILED (bool): Default tiling setting (True).
    DEFAULT_BIGTIFF (str): Default BigTIFF setting ("YES").
    DEFAULT_COMPRESSION (Compression): Default compression method (deflate).
    COG_PROFILE (CogProfile): Pre-configured COG profile instance.
    GEOTIFF_PROFILE (GeoTiffProfile): Pre-configured GeoTIFF profile instance.

Examples:
    Creating a COG from an existing raster:

    >>> import rasterio
    >>> from mypackage.raster_profiles import apply_cog_profile
    >>> with rasterio.open('source.tif') as src:
    ...     profile = src.profile
    ...     cog_profile = apply_cog_profile(profile)
    ...     cog_profile['driver']
    'COG'
    >>> cog_profile['compress']
    <Compression.deflate: 'deflate'>

    Using predefined profile instances:

    >>> from mypackage.raster_profiles import COG_PROFILE, GEOTIFF_PROFILE
    >>> COG_PROFILE['blocksize']
    512
    >>> GEOTIFF_PROFILE['tiled']
    True

    Customizing profiles for specific needs:

    >>> base_profile = {'width': 1000, 'height': 1000, 'count': 3}
    >>> cog_profile = apply_cog_profile(base_profile)
    >>> # COG-incompatible parameters are automatically removed
    >>> 'blockxsize' in cog_profile
    False
    >>> 'blocksize' in cog_profile
    True

Note:
    COG profiles automatically remove parameters that are incompatible with
    the COG driver (blockxsize, blockysize, tiled, interleave) to prevent
    rasterio errors during file creation.

    All profiles use deflate compression with level 9 by default for optimal
    file size, though this may increase processing time for very large datasets.
"""

from __future__ import annotations

from rasterio.enums import Compression
from rasterio.profiles import Profile

DEFAULT_BLOCK_SIZE = 512
DEFAULT_COMPRESS_Z_LEVEL = 9
DEFAULT_DRIVER_COG = "COG"
DEFAULT_DRIVER_GTIFF = "GTiff"
DEFAULT_INTERLEAVE = "pixel"
DEFAULT_TILED = True
DEFAULT_BIGTIFF = "YES"
DEFAULT_COMPRESSION = Compression.deflate


class CogProfile(Profile):
    """COG (cloud optimized GeoTiff) raster image settings."""

    defaults = {
        "bigtiff": DEFAULT_BIGTIFF,
        "blocksize": DEFAULT_BLOCK_SIZE,
        "compress": DEFAULT_COMPRESSION,
        "driver": DEFAULT_DRIVER_COG,
        "level": DEFAULT_COMPRESS_Z_LEVEL,
        "overview_resampling": "nearest",
        "predictor": "standard",
    }


class GeoTiffProfile(Profile):
    """GeoTiff raster image structure profile settings."""

    defaults = {
        "bigtiff": DEFAULT_BIGTIFF,
        "blockxsize": DEFAULT_BLOCK_SIZE,
        "blockysize": DEFAULT_BLOCK_SIZE,
        "compress": DEFAULT_COMPRESSION,
        "driver": DEFAULT_DRIVER_GTIFF,
        "interleave": "pixel",
        "tiled": DEFAULT_TILED,
        "zlevel": DEFAULT_COMPRESS_Z_LEVEL,
    }


COG_PROFILE = CogProfile()
GEOTIFF_PROFILE = GeoTiffProfile()


def apply_cog_profile(profile: Profile) -> Profile:
    """Apply COG profile settings to an existing raster profile.

    Takes an existing raster profile and applies COG-specific optimizations,
    automatically removing parameters that are incompatible with the COG driver.
    This ensures the resulting profile can be used successfully with rasterio
    to create COG files.

    The function filters out blockxsize, blockysize, tiled, and interleave
    parameters since the COG driver manages these automatically and will
    raise errors if they are manually specified.

    Args:
        profile (Profile): araster profile object.

    Returns:
        Profile: raster profile with the default COG profile applied.
    """
    invalid_cog_keys = ["blockxsize", "blockysize", "tiled", "interleave"]
    ok_cog_profile = {k: v for k, v in profile.items() if k not in invalid_cog_keys}

    return Profile({**ok_cog_profile, **COG_PROFILE})


def apply_geotiff_profile(profile: Profile) -> Profile:
    """Apply GeoTIFF profile settings to an existing raster profile.

    Takes an existing raster profile and applies standard GeoTIFF optimizations
    including tiling, compression, and performance settings. The input profile
    parameters are preserved and merged with GeoTIFF defaults, with defaults
    taking precedence for optimization parameters.

    This function is useful for standardizing GeoTIFF creation across different
    workflows while preserving essential raster metadata like dimensions,
    coordinate reference system, and data types from the source data.
    """
    return Profile({**profile, **GEOTIFF_PROFILE})

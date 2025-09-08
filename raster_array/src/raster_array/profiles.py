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
    """Apply the default COG profile to the given profile.

    Args:
        profile (Profile): araster profile object.

    Returns:
        Profile: raster profile with the default COG profile applied.
    """
    # these values aren't allowed using the COG driver
    invalid_cog_keys = ["blockxsize", "blockysize", "tiled", "interleave"]
    ok_cog_profile = {k: v for k, v in profile.items() if k not in invalid_cog_keys}

    return Profile({**ok_cog_profile, **COG_PROFILE})


def apply_geotiff_profile(profile: Profile) -> Profile:
    """Apply the default GeoTiff profile to the given profile.

    Args:
        profile (Profile): a raster profile object.

    Returns:
        Profile: raster profile with the default GeoTiff profile applied.
    """
    return Profile({**profile, **GEOTIFF_PROFILE})

"""Raster metadata management.

This module provides the RasterMetadata class, which stores and manages
geospatial raster metadata including coordinate reference system, dimensions,
data type, and geospatial transformation information. The class is designed
to work seamlessly with rasterio profiles.

Classes:
    RasterMetadata: A container for raster metadata, similar to a
        `rasterio.profiles.Profile`.

Examples:
    >>> from rasterio.crs import CRS
    >>> from rasterio.transform import from_bounds
    >>> import numpy as np
    >>>
    >>> # Create metadata for a basic raster
    >>> crs = CRS.from_epsg(4326)
    >>> transform = from_bounds(-180, -90, 180, 90, 360, 180)
    >>> metadata = RasterMetadata(
    ...     crs=crs,
    ...     count=3,
    ...     width=360,
    ...     height=180,
    ...     dtype=np.float32,
    ...     nodata=-9999,
    ...     transform=transform,
    ...     resolution=1.0
    ... )
"""

from __future__ import annotations

from operator import itemgetter

import rasterio
from geometry.crs import ensure_crs
from numpy.typing import DTypeLike
from pyproj import CRS
from rasterio.profiles import Profile
from rasterio.transform import array_bounds

from raster_array.profiles import apply_geotiff_profile

RASTER_BLOCK_SIZE = 512
RASTER_COMPRESS_Z_LEVEL = 9
RASTER_DRIVER_COG = "COG"
RASTER_DRIVER_GTIFF = "GTiff"
NO_RESOLUTION_SPECIFIED = 0


class RasterMetadata:
    """Container for geospatial raster metadata.

    This class encapsulates all the essential metadata needed to describe a
    geospatial raster dataset, including spatial reference information,
    dimensions, data type, and transformation parameters. It serves as a
    convenient wrapper around the core metadata concepts used by rasterio
    while providing additional functionality for raster array operations.

    Attributes:
        crs (CRS): Coordinate Reference System of the raster data.
        count (int): Number of bands in the raster dataset.
        width (int): Width of the raster in pixels (number of columns).
        height (int): Height of the raster in pixels (number of rows).
        dtype (DTypeLike): NumPy data type of the raster values.
        nodata (int | float): Value used to represent missing or invalid data.
        transform (rasterio.Affine): Affine transformation matrix mapping
            pixel coordinates to geographic coordinates.
        resolution (int | float): Spatial resolution of the raster. Defaults
            to NO_RESOLUTION_SPECIFIED if not provided.
    """

    crs: CRS
    count: int
    width: int
    height: int
    dtype: DTypeLike
    nodata: int | float
    transform: rasterio.Affine
    resolution: int | float = NO_RESOLUTION_SPECIFIED

    def __init__(
        self,
        crs: CRS,
        count: int,
        width: int,
        height: int,
        dtype: DTypeLike,
        nodata: int | float,
        transform: rasterio.Affine,
        resolution: int | float = NO_RESOLUTION_SPECIFIED,
    ):
        """Initialize a RasterMetadata object.

        Attributes:
            crs (CRS): Coordinate Reference System of the raster data.
            count (int): Number of bands in the raster dataset.
            width (int): Width of the raster in pixels (number of columns).
            height (int): Height of the raster in pixels (number of rows).
            dtype (DTypeLike): NumPy data type of the raster values.
            nodata (int | float): Value used to represent missing or invalid data.
            transform (rasterio.Affine): Affine transformation matrix mapping
                pixel coordinates to geographic coordinates.
            resolution (int | float): Spatial resolution of the raster. Defaults
                to NO_RESOLUTION_SPECIFIED if not provided.
        """
        self.crs = ensure_crs(crs)
        self.count = count
        self.width = width
        self.height = height
        self.dtype = dtype
        self.nodata = nodata
        self.transform = transform
        self.resolution = resolution

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """Return the bounds of the raster.

        Returns:
            tuple[float, float, float, float]: Bounding box as (left, bottom, right, top).
        """
        return array_bounds(self.width, self.height, self.transform)

    @property
    def profile(self) -> Profile:
        """Return a raster profile.

        Returns:
            Profile: Rasterio profile with GeoTIFF settings applied.
        """
        profile_fields = [
            "crs",
            "count",
            "dtype",
            "nodata",
            "width",
            "height",
            "transform",
        ]
        profile_values = itemgetter(*profile_fields)(self.__dict__)
        profile = Profile(dict(zip(profile_fields, profile_values)))
        return apply_geotiff_profile(profile)

    @property
    def shape(self) -> tuple[int, int, int]:
        """Return the shape of the raster.

        Returns:
            tuple[int, int, int]: Shape as (count, height, width).
        """
        return (self.count, self.height, self.width)

    # methods ---------------------------------------------------------------------
    def copy(self, **kwargs) -> RasterMetadata:
        """Create a copy of this RasterMetadata with optional modifications.

        This method creates a new RasterMetadata object with the same values as the
        current one, but allows you to override specific attributes. This is useful
        when you need to create a modified version without specifying all parameters.

        Args:
            **kwargs: Keyword arguments for any RasterMetadata attributes to override.
                Valid keys include: crs, count, width, height, dtype, nodata,
                transform, and resolution. Invalid keys are ignored.

        Returns:
            RasterMetadata: A new RasterMetadata object with updated values.

        Examples:
            >>> # Create a copy with different dtype and nodata
            >>> new_metadata = metadata.copy(dtype=np.int16, nodata=-32767)
            >>>
            >>> # Create a copy with different CRS
            >>> reprojected = metadata.copy(crs=CRS.from_epsg(3857))
        """
        current_items = self.__dict__
        allowed_keys_in_kwargs = set(current_items.keys()) & set(kwargs.keys())
        new_items = {key: kwargs[key] for key in allowed_keys_in_kwargs}
        merged_items = {**current_items, **new_items}
        return RasterMetadata(**merged_items)  # ty: ignore

    # @staticmethods --------------------------------------------------------------
    @staticmethod
    def from_profile(profile: Profile) -> RasterMetadata:
        """Create a RasterMetadata object from a rasterio profile.

        Args:
            profile (Profile): Rasterio profile containing raster metadata.

        Returns:
            RasterMetadata: New RasterMetadata object with values from the profile.
        """
        profile_fields = [
            "crs",
            "count",
            "dtype",
            "nodata",
            "width",
            "height",
            "transform",
        ]
        profile_values = itemgetter(*profile_fields)(profile)
        return RasterMetadata(**dict(zip(profile_fields, profile_values)))  # ty: ignore

    @staticmethod
    def from_raster(raster: str | rasterio.DatasetReader) -> RasterMetadata:
        if isinstance(raster, rasterio.DatasetReader):
            return RasterMetadata._from_datasetreader(raster)

        with rasterio.open(raster) as src:
            return RasterMetadata._from_datasetreader(src)

    @staticmethod
    def _from_datasetreader(src: rasterio.DatasetReader) -> RasterMetadata:
        return RasterMetadata.from_profile(src.profile)

    # Magic methods (dunder methods) ----------------------------------------------
    def __repr__(self):
        """Return string representation of the RasterMetadata."""
        crs_repr = self.crs.to_string()
        transform_repr = self.transform.__repr__().replace("\n      ", "")
        return f"RasterMetadata(crs={crs_repr}, count={self.count}, width={self.width}, height={self.height}, dtype={self.dtype!r}, nodata={self.nodata}, transform={transform_repr}, resolution={self.resolution})"

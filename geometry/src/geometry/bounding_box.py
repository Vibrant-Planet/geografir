"""Bounding box implementation with coordinate reference system support.

This module provides a BoundingBox class for representing rectangular extents
of geometries with proper CRS (Coordinate Reference System) information. The
BoundingBox class integrates seamlessly with pyproj for CRS handling and supports
creation from both geometry objects and direct coordinate specification.

Classes:
    BoundingBox: A rectangular extent with CRS information.

Examples:
    Basic bounding box operations:

    >>> from geometry.bbox import BoundingBox
    >>> from geometry import Geometry
    >>> from shapely.geometry import Polygon
    >>>
    >>> # Create bounding box from coordinates
    >>> bbox = BoundingBox(-122.5, 37.7, -122.4, 37.8, "EPSG:4326")
    >>> print(f"Area covers: {list(bbox)}")
    >>>
    >>> # Create from geometry
    >>> poly = Polygon([(-122.5, 37.7), (-122.4, 37.7),
    ...                 (-122.4, 37.8), (-122.5, 37.8)])
    >>> geom = Geometry(poly, crs="EPSG:4326")
    >>> bbox_from_geom = BoundingBox.from_geometry(geom)

    Working with different coordinate systems:

    >>> # Web Mercator bounding box
    >>> web_mercator_bbox = BoundingBox(
    ...     -13638851.05, 4539747.77, -13629765.94, 4548832.89,
    ...     "EPSG:3857"
    ... )
    >>>
    >>> # UTM Zone 10N bounding box
    >>> utm_bbox = BoundingBox(
    ...     500000, 4170000, 510000, 4180000,
    ...     "EPSG:32610"
    ... )

Note:
    Coordinate values are stored as provided and are not validated for CRS
    appropriateness. Users should ensure coordinates match the specified CRS.

    This module uses pyproj for CRS handling. The pyproj CRS class is mostly
    compatible with the rasterio.CRS module. The two can almost always be used
    interchangeably.
"""

from __future__ import annotations
from pyproj import CRS
from typing import Iterator

from geometry.crs import ensure_crs

from geometry.geometry import Geometry


class BoundingBox:
    """Represents the rectangular extent of a geometry with CRS information.

    A bounding box defines the rectangular extent of a geometry using minimum
    and maximum x and y coordinates, along with coordinate reference system (CRS)
    information for proper spatial context.

    Attributes:
        minx (int | float): The minimum x-coordinate (western/left boundary) of
            the bounding box. Represents the smallest longitude in geographic
            coordinate systems or the leftmost easting in projected systems.
        miny (int | float): The minimum y-coordinate (southern/bottom boundary) of
            the bounding box. Represents the smallest latitude in geographic
            coordinate systems or the bottommost northing in projected systems.
        maxx (int | float): The maximum x-coordinate (eastern/right boundary) of
            the bounding box. Represents the largest longitude in geographic
            coordinate systems or the rightmost easting in projected systems.
        maxy (int | float): The maximum y-coordinate (northern/top boundary) of
            the bounding box. Represents the largest latitude in geographic
            coordinate systems or the topmost northing in projected systems.
        crs (CRS): The coordinate reference system of the bounding box as a
            pyproj.CRS object.

    Note:
        Coordinates are stored exactly as provided without validation against
        the specified CRS. Users are responsible for ensuring coordinate values
        are appropriate for their chosen coordinate system.
    """

    minx: int | float
    miny: int | float
    maxx: int | float
    maxy: int | float
    crs: CRS | int | str

    def __init__(
        self,
        minx: int | float,
        miny: int | float,
        maxx: int | float,
        maxy: int | float,
        crs: CRS | int | str,
    ):
        """Initialize a BoundingBox object.

        Args:
            minx (int | float): The minimum x-coordinate (western/left boundary) of
                the bounding box. Represents the smallest longitude in geographic
                coordinate systems or the leftmost easting in projected systems.
            miny (int | float): The minimum y-coordinate (southern/bottom boundary) of
                the bounding box. Represents the smallest latitude in geographic
                coordinate systems or the bottommost northing in projected systems.
            maxx (int | float): The maximum x-coordinate (eastern/right boundary) of
                the bounding box. Represents the largest longitude in geographic
                coordinate systems or the rightmost easting in projected systems.
            maxy (int | float): The maximum y-coordinate (northern/top boundary) of
                the bounding box. Represents the largest latitude in geographic
                coordinate systems or the topmost northing in projected systems.
            crs (CRS | int | str): The coordinate reference system specification.
                Accepts any format supported by `pyproj.CRS.from_user_input()`,
                including:
                - EPSG codes as integers (e.g., 4326) or strings (e.g., "EPSG:4326")
                - PROJ strings (e.g., "+proj=longlat +datum=WGS84")
                - WKT (Well-Known Text) definitions
                - pyproj.CRS objects (passed through directly)
                - Authority:Code format (e.g., "EPSG:4326", "ESRI:102001")

        Raises:
            pyproj.exceptions.CRSError: If the CRS specification cannot be
                interpreted by pyproj. This includes invalid EPSG codes,
                malformed PROJ strings, or unsupported CRS definitions.
        """
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.crs = ensure_crs(crs)

    @staticmethod
    def from_geometry(geometry: Geometry) -> BoundingBox:
        """Create a BoundingBox from a Geometry object's spatial extent.

        Extracts the minimum bounding rectangle from a Geometry object and creates
        a new BoundingBox instance with the same coordinate reference system.

        Args:
            geometry (Geometry): The geometry object from which to extract the
                bounding box. Must be a valid Geometry instance with a defined
                spatial extent and coordinate reference system. The geometry's
                underlying shapely object must support the `.bounds` property,
                which returns (minx, miny, maxx, maxy) coordinates. Empty or
                null geometries may produce unexpected results.

        Returns:
            BoundingBox: A new BoundingBox instance. The returned bounding
                box inherits the CRS from the input geometry.

        Examples:
            Create bounding box from a point geometry:

            >>> from geometry import Geometry
            >>> from shapely.geometry import Point
            >>> geom = Geometry(Point(-122.4, 37.8), crs="EPSG:4326")
            >>> bbox = BoundingBox.from_geometry(geom)
            >>> print(list(bbox))
            [-122.4, 37.8, -122.4, 37.8]
        """
        minx, miny, maxx, maxy = geometry.geometry.bounds

        return BoundingBox(minx, miny, maxx, maxy, crs=geometry.crs)

    # Magic methods (dunder methods) ----------------------------------------------
    def __iter__(self) -> Iterator[int | float]:
        """Yield coordinate values in standard [minx, miny, maxx, maxy] order."""
        return iter((self.minx, self.miny, self.maxx, self.maxy))

    def __repr__(self) -> str:
        """Return string representation of the BoundingBox."""
        crs_repr = self.crs.to_string()
        return f"BoundingBox(minx={self.minx}, miny={self.miny}, maxx={self.maxx}, maxy={self.maxy}, crs='{crs_repr}')"

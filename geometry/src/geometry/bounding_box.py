"""Bounding box implementation with coordinate reference system support.

This module provides the BoundingBox class for representing rectangular extents
of geometries with proper CRS (Coordinate Reference System) information. The
BoundingBox class integrates with pyproj for CRS handling and can be created
from geometry objects or coordinate values directly.

Classes:
    BoundingBox: A rectangular extent with CRS information that supports
        iteration and conversion to coordinate lists.
"""

from __future__ import annotations
from pyproj import CRS
from typing import Iterator

from geometry.crs import ensure_crs

from geometry.geometry import Geometry


class BoundingBox:
    """Represents the bounding box of a geometry with CRS information.

    A bounding box defines the rectangular extent of a geometry using minimum
    and maximum x and y coordinates, along with coordinate reference system (CRS)
    information for proper spatial context.

    Attributes:
        minx (int | float): The minimum x-coordinate of the bounding box.
        miny (int | float): The minimum y-coordinate of the bounding box.
        maxx (int | float): The maximum x-coordinate of the bounding box.
        maxy (int | float): The maximum y-coordinate of the bounding box.
        crs (CRS): The coordinate reference system of the bounding box.

    Examples:
        Create a bounding box from coordinates:

        >>> bbox = BoundingBox(-122.5, 37.7, -122.4, 37.8, "EPSG:4326")
        >>> print(bbox)
        BoundingBox(minx=-122.5, miny=37.7, maxx=-122.4, maxy=37.8, crs='EPSG:4326')

        Convert to list for coordinate processing:

        >>> coords = list(bbox)
        >>> print(coords)
        [-122.5, 37.7, -122.4, 37.8]

        Unpack coordinates:

        >>> minx, miny, maxx, maxy = bbox
        >>> print(f"Width: {maxx - minx}, Height: {maxy - miny}")
        Width: 0.1, Height: 0.1
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
            minx (int | float): The minimum x-coordinate of the bounding box.
            miny (int | float): The minimum y-coordinate of the bounding box.
            maxx (int | float): The maximum x-coordinate of the bounding box.
            maxy (int | float): The maximum y-coordinate of the bounding box.
            crs (CRS | int | str): The coordinate reference system of the bounding
                box. This will be handled by `pyproj.CRS.from_user_input`. Any value
                accepted by `pyproj.CRS.from_user_input` is valid.
        """
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.crs = ensure_crs(crs)

    @staticmethod
    def from_geometry(geometry: Geometry) -> BoundingBox:
        """Create a BoundingBox from a Geometry object.

        Args:
            geometry (Geometry): The geometry to create the bounding box from.

        Returns:
            BoundingBox: The bounding box of the geometry with the same CRS.

        Examples:
            Create bounding box from a point geometry:

            >>> from geometry.geometry import Geometry
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
        """Yield coordinates as [minx, miny, maxx, maxy]."""
        return iter((self.minx, self.miny, self.maxx, self.maxy))

    def __repr__(self) -> str:
        """Return string representation of the BoundingBox."""
        crs_repr = self.crs.to_string()
        return f"BoundingBox(minx={self.minx}, miny={self.miny}, maxx={self.maxx}, maxy={self.maxy}, crs='{crs_repr}')"

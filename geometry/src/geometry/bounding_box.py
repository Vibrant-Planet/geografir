"""
A bounding box of a geometry with CRS information.
"""

from __future__ import annotations
from pyproj import CRS

from geometry.crs import ensure_crs

from geometry.geometry import Geometry


class BoundingBox:
    """Represents the bounding box of a geometry with CRS information."""

    minx: float
    miny: float
    maxx: float
    maxy: float
    crs: CRS | int | str

    def __init__(
        self, minx: float, miny: float, maxx: float, maxy: float, crs: CRS | int | str
    ):
        """Initialize a BoundingBox object.

        Args:
            minx (float): The minimum x-coordinate of the bounding box.
            miny (float): The minimum y-coordinate of the bounding box.
            maxx (float): The maximum x-coordinate of the bounding box.
            maxy (float): The maximum y-coordinate of the bounding box.
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
            BoundingBox: The bounding box of the geometry.
        """
        minx, miny, maxx, maxy = geometry.geometry.bounds

        return BoundingBox(minx, miny, maxx, maxy, crs=geometry.crs)

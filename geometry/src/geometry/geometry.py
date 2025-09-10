"""A simple geospatial geometry package wrapping Shapely geometries with CRS information.

This module provides the Geometry class which combines Shapely's powerful geometry
objects with coordinate reference system (CRS) information from pyproj. This enables
proper geospatial operations including coordinate transformations and projections
while maintaining the rich geometric capabilities of Shapely.

Classes:
    Geometry: A wrapper that combines Shapely geometries with CRS information
        for geospatial operations and coordinate transformations.
"""

from __future__ import annotations

from shapely.geometry.base import BaseGeometry
from shapely import ops

from pyproj import CRS
from pyproj import Transformer

from geometry.exceptions import TransformError
from geometry.crs import ensure_crs


class Geometry:
    """A geospatial geometry wrapper that combines Shapely geometries with CRS information.

    This class wraps a Shapely BaseGeometry object and associates it with a coordinate
    reference system (CRS) to enable geospatial operations like reprojection, coordinate
    transformation, and proper spatial analysis. Full Shapely functionality is deferred to
    the underlying Shapely geometry object.

    Attributes:
        geometry (BaseGeometry): The underlying Shapely geometry object (Point, LineString,
            Polygon, etc.).
        crs (CRS): The coordinate reference system as a pyproj CRS object.

    Examples:
        Create geometry from different Shapely objects:

        >>> import shapely as sp
        >>> from shapely import Point, LineString, Polygon
        >>> from geometry import Geometry

        Point geometry:
        >>> point = Point(-73.9857, 40.7484)
        >>> geom = Geometry(point, "EPSG:4326")
        >>> print(f"Coordinates: {geom.geometry.x}, {geom.geometry.y}")
        Coordinates: -73.9857, 40.7484

        LineString geometry:
        >>> line = LineString([(-74.0, 40.7), (-73.9, 40.8)])
        >>> geom = Geometry(line, 4326)
        >>> print(f"Length: {geom.geometry.length:.6f} degrees")
        Length: 0.141421 degrees

        Polygon geometry with UTM projection:
        >>> coords = [(500000, 4000000), (600000, 4000000), (600000, 4100000), (500000, 4100000), (500000, 4000000)]
        >>> polygon = Polygon(coords)
        >>> geom = Geometry(polygon, "EPSG:32633")  # UTM Zone 33N
        >>> print(f"Area: {geom.geometry.area} square meters")
        Area: 10000000000.0 square meters

        Use Shapely on the geometry:
        >>> print(sp.get_coordinates(geom.geometry))
        [[500000.0, 4000000.0], [600000.0, 4000000.0], [600000.0, 4100000.0], [500000.0, 4100000.0], [500000.0, 4000000.0]]

        Access CRS information:
        >>> print(geom.crs.to_string())
        'EPSG:32633'
        >>> print(geom.crs.is_projected)
        True
    """

    geometry: BaseGeometry
    crs: CRS

    def __init__(self, geometry: BaseGeometry, crs: CRS | int | str):
        """Initialize a Geometry object with a Shapely geometry and CRS.

        Args:
            geometry (BaseGeometry): A Shapely geometry object (Point, LineString,
                Polygon, MultiPoint, MultiLineString, MultiPolygon, or GeometryCollection).
            crs (CRS | int | str): Coordinate reference system. Can be a pyproj CRS
                object, EPSG code as integer, or any string format accepted by
                `pyproj.CRS.from_user_input()` (e.g., "EPSG:4326", "WGS84", proj4 string).

        Raises:
            TypeError: If geometry is not a Shapely BaseGeometry instance.
            ValueError: If CRS cannot be parsed by pyproj.
        """
        if not isinstance(geometry, BaseGeometry):
            raise TypeError(
                f"geometry must be a Shapely BaseGeometry, got {type(geometry)}"
            )

        self.geometry = geometry
        self.crs = ensure_crs(crs)

    # Methods ------------------------------------------------------------------
    def to_crs(self, crs: CRS | int | str) -> Geometry:
        """Convert the geometry to a different coordinate reference system.

        Args:
            crs (CRS | int | str): Coordinate reference system. Can be a pyproj CRS
                object, EPSG code as integer, or any string format accepted by
                `pyproj.CRS.from_user_input()` (e.g., "EPSG:4326", "WGS84", proj4 string).

        Returns:
            Geometry: A new Geometry object with the converted geometry and CRS.
        """
        target_crs = ensure_crs(crs)

        if self.crs.equals(target_crs):
            return self

        # create transform object (this can fail if transforming between incompatible projects, this should be rare)
        try:
            transformer = Transformer.from_crs(self.crs, target_crs, always_xy=True)
        except Exception as e:
            raise TransformError(
                f"Cannot create transformation from {self.crs} to {target_crs}"
            ) from e

        # then apply transform
        transformed_geometry = ops.transform(transformer.transform, self.geometry)
        return Geometry(transformed_geometry, target_crs)

    # Magic methods (dunder methods) -------------------------------------------
    def __repr__(self) -> str:
        """Return string representation of the BoundingBox."""
        crs_repr = self.crs.to_string()
        return f"Geometry(geometry={self.geometry!r}, crs='{crs_repr}')"

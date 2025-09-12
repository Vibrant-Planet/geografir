"""A geospatial geometry package wrapping Shapely geometries with CRS information.

This module provides the foundational Geometry class that bridges the gap between
Shapely's geometric operations and proper geospatial coordinate reference
system (CRS) handling. Combining Shapely's geometry capabilities with pyproj's
coordinate system management, this package enables accurate geospatial analysis,
coordinate transformations, and spatial operations while maintaining geometric
precision and spatial context.

Classes:
    Geometry: A geospatial wrapper that combines Shapely BaseGeometry objects
        with coordinate reference system information to enable proper spatial
        operations, coordinate transformations, and geographic analysis.

Examples:
    Working with different geometry types and coordinate systems:

    >>> from geometry import Geometry
    >>> from shapely import Point, LineString, Polygon, MultiPoint
    >>>
    >>> point_a = Geometry(Point(-122.4194, 37.7749), "EPSG:4326")
    >>> point_b = Geometry(Point(-118.2437, 34.0522), "EPSG:4326")
    >>>
    >>> line = LineString([point_a.geometry, point_b.geometry])
    >>> line_geom = Geometry(line, "EPSG:4326")
    >>>
    >>> # Transform to equal-area projection for accurate distance
    >>> line_projected = line_geom.to_crs("EPSG:3310")
    >>> distance_km = line_projected.geometry.length / 1000
    >>> print(f"Distance: {distance_km:.1f} km")

    Coordinate system transformations and projections:

    >>> # Create geometry in one coordinate system
    >>> wgs84_point = Geometry(Point(-122.4, 37.8), "EPSG:4326")
    >>>
    >>> # Transform to various coordinate systems
    >>> utm_point = wgs84_point.to_crs("EPSG:32610")      # UTM Zone 10N
    >>> mercator_point = wgs84_point.to_crs("EPSG:3857")  # Web Mercator
    >>> albers_point = wgs84_point.to_crs("EPSG:3310")    # California Albers
    >>>
    >>> # Access transformed coordinates
    >>> print(f"UTM: {utm_point.geometry.x:.1f}, {utm_point.geometry.y:.1f}")
    >>> print(f"Web Mercator: {mercator_point.geometry.x:.1f}, {mercator_point.geometry.y:.1f}")

    Integration with Shapely operations:

    >>> # Use full Shapely functionality while maintaining CRS
    >>> point1 = Geometry(Point(0, 0), "EPSG:4326")
    >>> point2 = Geometry(Point(1, 1), "EPSG:4326")
    >>>
    >>> # Shapely geometric operations
    >>> distance = point1.geometry.distance(point2.geometry)
    >>> contains = point1.geometry.within(point2.geometry.buffer(2))
    >>>
    >>> import shapely as sp
    >>> coords = sp.get_coordinates(line_geom.geometry)
    >>> centroid = line_geom.geometry.centroid
    >>> bounds = line_geom.geometry.bounds

Note:
    The Geometry class maintains the full interface of Shapely geometries through
    the .geometry attribute, ensuring complete compatibility with existing Shapely
    workflows while adding essential geospatial capabilities.

    Coordinate transformations preserve geometric relationships and topology but
    may introduce small numerical differences due to projection mathematics.
    Consider appropriate coordinate systems for your analysis requirements.
    Coordinate transformations between significantly different coordinate systems
    (e.g., local projections to global systems) may fail entirely if the
    transformations between CRSs are not compatible.

    The module assumes input geometries have coordinates that are valid for their
    specified coordinate reference system. Invalid coordinates may produce
    unexpected results during transformations.

See Also:
    geometry.crs.ensure_crs: CRS normalization and validation function.
    shapely.geometry.base.BaseGeometry: Base class for all Shapely geometries.
    pyproj.CRS: Coordinate reference system handling and transformations.
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
        geometry (BaseGeometry): The underlying Shapely geometry object providing
            comprehensive geometric operations. Can be any Shapely geometry type:
            Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon,
            or GeometryCollection.
        crs (CRS): The coordinate reference system as a pyproj CRS object that
            defines the spatial context of the geometry coordinates.
    """

    geometry: BaseGeometry
    crs: CRS

    def __init__(self, geometry: BaseGeometry, crs: CRS | int | str):
        """Initialize a Geometry object with a Shapely geometry and coordinate reference system.

        The constructor performs minimal processing to preserve the exact
        Shapely geometry provided. Geometric validation, if needed, should
        be performed using Shapely's validation methods on the .geometry
        attribute.

        CRS validation and normalization ensures the coordinate system
        context is properly established but does not verify that geometry
        coordinates are appropriate for the specified CRS.

        Args:
            geometry (BaseGeometry): A Shapely geometry object representing the
                spatial feature. Must be an instance of shapely.geometry.base.BaseGeometry.
                The geometry can be empty, valid, or invalid according to Shapely's
                validation rules. All geometric properties and operations are
                delegated to this underlying Shapely object.

            crs (CRS | int | str): Coordinate reference system specification that
                defines the spatial context of the geometry coordinates. Accepts
                multiple input formats for maximum flexibility:
                - pyproj.CRS objects: Direct CRS instances with full metadata
                - Integer EPSG codes: Numeric identifiers (e.g., 4326, 3857, 32610)
                - String specifications: Various string formats including:
                    - EPSG format: "EPSG:4326", "epsg:4326"
                    - PROJ strings: "+proj=longlat +datum=WGS84 +no_defs"
                    - WKT definitions: Complete Well-Known Text coordinate system
                    - Authority codes: "ESRI:102001", "NAD83:4269"
                    - Common names: "WGS84", "NAD83"

                The CRS is processed through geometry.crs.ensure_crs() for
                validation and normalization, ensuring consistent handling
                across the geometry module ecosystem.

        Raises:
            CRSError: Raised by the underlying pyproj library when CRS
                processing fails
        """
        if not isinstance(geometry, BaseGeometry):
            raise TypeError(
                f"geometry must be a Shapely BaseGeometry, got {type(geometry)}"
            )

        self.geometry = geometry
        self.crs = ensure_crs(crs)

    # Methods ------------------------------------------------------------------
    def to_crs(self, crs: CRS | int | str) -> Geometry:
        """Transform the geometry to a different coordinate reference system.

        Performs coordinate transformation from the current CRS to the specified
        target CRS, creating a new Geometry object with transformed coordinates
        and updated CRS information. This method enables accurate spatial analysis
        across different coordinate systems and map projections while preserving
        geometric relationships and topology. The transformation process uses
        pyproj's coordinate transformation capabilities.

        Coordinate transformations preserve geometric topology but may
        introduce small numerical variations. Transformations between coordinate
        systems with significantly different characteristics may introduce
        distortions or fail entirely. Always validate transformation results for
        your specific use case and consider the appropriate coordinate system
        for your analysis needs.

        The transformation uses pyproj's "always_xy=True" parameter to ensure
        consistent coordinate ordering regardless of the CRS axis definition.

        Args:
            crs (CRS | int | str): The target coordinate reference system for
                transformation. Accepts the same input formats as the Geometry
                constructor.

        Returns:
            Geometry: A new Geometry object containing the transformed geometry
                coordinates in the target coordinate reference system.

                If the source and target CRS are equivalent (determined by
                pyproj.CRS.equals()), the original Geometry object is returned
                unchanged for efficiency, avoiding unnecessary computation.

        Raises:
            TransformError: Raised when coordinate transformation fails.
            CRSError: Raised indirectly through ensure_crs() if the target CRS
                specification cannot be parsed or validated by pyproj.


        Examples:
            Transform between common coordinate systems:

            >>> from shapely import Point
            >>> from geometry import Geometry

            Geographic to projected transformation:
            >>> # WGS84 geographic coordinates (degrees)
            >>> geo_point = Geometry(Point(-122.4194, 37.7749), "EPSG:4326")
            >>> # Transform to UTM Zone 10N (meters)
            >>> utm_point = geo_point.to_crs("EPSG:32610")
            >>> print(f"UTM: {utm_point.geometry.x:.1f}, {utm_point.geometry.y:.1f}")
            UTM: 551072.8, 4180835.5

            Projected to geographic transformation:
            >>> # UTM coordinates (meters)
            >>> utm_geom = Geometry(Point(551072, 4180835), "EPSG:32610")
            >>> # Transform to WGS84 (degrees)
            >>> geo_geom = utm_geom.to_crs(4326)
            >>> print(f"Lat/Lon: {geo_geom.geometry.y:.6f}, {geo_geom.geometry.x:.6f}")
            Lat/Lon: 37.774895, -122.419438
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
        """Return string representation of the Geometry."""
        crs_repr = self.crs.to_string()
        return f"Geometry(geometry={self.geometry!r}, crs='{crs_repr}')"

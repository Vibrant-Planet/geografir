"""
A simple geospatial geometry package wrapping Shapely geometries with CRS information.
"""

from shapely.geometry.base import BaseGeometry

from pyproj import CRS
from pyproj.exceptions import CRSError


class Geometry:
    """
    A geospatial geometry wrapper that combines Shapely geometries with CRS information.

    This class wraps a Shapely BaseGeometry object and associates it with a coordinate
    reference system (CRS) to enable geospatial operations like reprojection.

    Attributes:
        geometry: The underlying Shapely geometry object
        crs: The coordinate reference system as a pyproj CRS object
    """

    geometry: BaseGeometry
    crs: CRS

    def __init__(self, geometry, crs):
        """
        Initialize a Geometry object.

        Args:
            geometry: A Shapely geometry object
            crs: Coordinate reference system. Can be a pyproj CRS or EPSG code.

        Raises:
            TypeError: If geometry is not a Shapely BaseGeometry
            ValueError: If CRS cannot be parsed
        """
        if not isinstance(geometry, BaseGeometry):
            raise TypeError(
                f"geometry must be a Shapely BaseGeometry, got {type(geometry)}"
            )
        self.geometry = geometry

        # Convert CRS to pyproj CRS object if needed
        if isinstance(crs, CRS):
            self.crs = crs
        else:
            try:
                self.crs = CRS.from_user_input(crs)
            except CRSError as e:
                raise ValueError(f"Invalid CRS specification: {crs}") from e

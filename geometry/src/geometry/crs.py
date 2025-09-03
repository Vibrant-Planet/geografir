"""CRS module

This module provides utility functions for working with `pyproj` coordinate reference systems (CRS).
"""

from pyproj import CRS
from pyproj.exceptions import CRSError


def ensure_crs(crs: CRS | str | int) -> CRS:
    """
    Convert various CRS representations to a pyproj CRS object.

    Args:
        crs: CRS specification as a CRS object, string, or integer

    Returns:
        CRS: A pyproj CRS object

    Raises:
        CRSError: If the crs cannot be converted to a valid CRS

    Examples:
        >>> ensure_crs("EPSG:4326")
        <Projected CRS: EPSG:4326>

        >>> ensure_crs(4326)
        <Projected CRS: EPSG:4326>

        >>> crs = CRS.from_epsg(4326)
        ensure_crs(crs)
        <Projected CRS: EPSG:4326>
    """
    if isinstance(crs, CRS):
        return crs

    try:
        return CRS.from_user_input(crs)
    except CRSError as e:
        raise CRSError(f"Invalid target CRS specification: {crs}") from e

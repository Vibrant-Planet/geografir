"""CRS utility module for coordinate reference system handling.

This module provides essential utility functions for working with pyproj coordinate
reference systems (CRS) in a standardized and error-resilient manner. It serves
as a normalization layer that accepts various CRS input formats and ensures
consistent pyproj.CRS object output throughout spatial data processing workflows.

Functions:
    ensure_crs: Converts various CRS representations (integers, strings, CRS objects)
        to standardized pyproj.CRS objects with comprehensive error handling and
        validation. This function serves as the primary entry point for CRS
        normalization throughout the geometry module ecosystem.

Examples:
    Basic CRS normalization from different input types:

    >>> # EPSG integer codes
    >>> wgs84 = ensure_crs(4326)
    >>> utm_10n = ensure_crs(32610)
    >>> web_mercator = ensure_crs(3857)
    >>>
    >>> # EPSG string specifications
    >>> wgs84_str = ensure_crs("EPSG:4326")
    >>> utm_str = ensure_crs("EPSG:32610")
    >>>
    >>> # PROJ string definitions
    >>> custom_proj = ensure_crs("+proj=longlat +datum=WGS84 +no_defs")
    >>> utm_proj = ensure_crs("+proj=utm +zone=10 +datum=WGS84")

Note:
    This module is designed as a lightweight utility layer and does not perform
    coordinate transformations or geometric operations. It focuses solely on
    CRS object normalization and validation.

Warning:
    CRS validation relies on pyproj's internal databases and may fail for
    custom or proprietary coordinate systems not recognized by PROJ. Users
    working with non-standard CRS definitions should ensure their PROJ
    installation includes necessary database updates.
"""

from pyproj import CRS
from pyproj.exceptions import CRSError


def ensure_crs(crs: CRS | str | int) -> CRS:
    """Convert various CRS representations to a standardized pyproj CRS object.

    this function accepts most common CRS input formats and ensures consistent
    pyproj.CRS object output, eliminating format inconsistencies and providing
    error handling for invalid specifications.

    The function safely handles properly formatted CRS objects (a no-op) while
    providing validation for string and integer inputs.

    Args:
        crs (CRS | str | int): The coordinate reference system specification to
            normalize. Accepts multiple input formats:
            - pyproj.CRS objects: Returned unchanged.
            - Integer EPSG codes: Common numeric identifiers for standard coordinate
                systems (e.g., 4326 for WGS84, 3857 for Web Mercator). Must be valid
                EPSG codes recognized by the pyproj PROJ database.
            - String specifications: Flexible string-based CRS definitions including:
                - EPSG format strings (e.g., "EPSG:4326", "epsg:4326")
                - PROJ parameter strings (e.g., "+proj=longlat +datum=WGS84")
                - WKT (Well-Known Text) coordinate system definitions
                - Authority:Code combinations (e.g., "ESRI:102001")
                - OGC URN format (e.g., "urn:ogc:def:crs:EPSG::4326")

            The function leverages `pyproj.CRS.from_user_input()` for maximum
            compatibility with diverse CRS specification formats.

    Returns:
        CRS: A validated pyproj.CRS object representing the specified coordinate
            reference system. The returned object provides access to all CRS
            properties. The CRS object can be used directly with pyproj transformation
            functions, spatial libraries, and geometry operations requiring
            coordinate system context.

    Raises:
        CRSError: Raised when the input CRS specification cannot be interpreted
            or validated by pyproj. Common causes include:
            - Invalid EPSG codes not found in the PROJ database
            - Malformed PROJ parameter strings with syntax errors
            - Unrecognized authority codes or coordinate system names
            - Corrupted or incomplete WKT definitions

    Examples:
        Normalize EPSG integer codes:

        >>> # Standard geographic coordinate system
        >>> wgs84 = ensure_crs(4326)
        >>> print(wgs84.name)
        WGS 84

        >>> # Projected coordinate system
        >>> utm_zone_10n = ensure_crs(32610)
        >>> print(utm_zone_10n.name)
        WGS 84 / UTM zone 10N

        Handle string EPSG specifications:

        >>> # Case-insensitive EPSG format
        >>> crs_upper = ensure_crs("EPSG:4326")
        >>> crs_lower = ensure_crs("epsg:4326")
        >>> assert crs_upper == crs_lower

        Work with PROJ parameter strings:

        >>> # Custom geographic coordinate system
        >>> custom_geo = ensure_crs("+proj=longlat +datum=WGS84 +no_defs")
        >>> print(custom_geo.to_authority())
        ('OGC', 'CRS84')

        >>> # UTM projection with specific parameters
        >>> utm_proj = ensure_crs("+proj=utm +zone=33 +datum=WGS84 +units=m +no_defs")

        Handle existing CRS objects (idempotent operation):

        >>> from pyproj import CRS
        >>> existing_crs = CRS.from_epsg(4326)
        >>> normalized_crs = ensure_crs(existing_crs)
        >>> assert existing_crs is normalized_crs  # Same object returned

    Warning:
        Some CRS definitions may require network access to resolve authority
        databases or download updated CRS parameters. Ensure appropriate network
        connectivity for production deployments. TODO: try to avoid making network
        requests by identifying these before the request is made. For most
        standard CRS this shouldn't be a problem.

        Custom or proprietary coordinate systems may not be recognized by the
        PROJ database. Consider updating PROJ data files or providing complete
        WKT definitions for non-standard coordinate systems.

    See Also:
        pyproj.CRS: The core CRS class for coordinate system representation.
        pyproj.CRS.from_user_input: The underlying function for CRS parsing.
    """
    if isinstance(crs, CRS):
        return crs

    try:
        return CRS.from_user_input(crs)
    except CRSError as e:
        raise CRSError(f"Invalid target CRS specification: {crs}") from e

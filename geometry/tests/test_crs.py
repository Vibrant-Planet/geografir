import pytest
from pyproj import CRS
from pyproj.exceptions import CRSError

from geometry.crs import ensure_crs


def test_crs_object_passthrough():
    original_crs = CRS.from_epsg(4326)
    result = ensure_crs(original_crs)

    # this tests that these are the exact same object, we might want a copy for safety?
    assert result is original_crs
    assert isinstance(result, CRS)


def test_epsg_string():
    result = ensure_crs("EPSG:4326")

    assert isinstance(result, CRS)
    assert result.to_epsg() == 4326


def test_epsg_integer():
    result = ensure_crs(4326)

    assert isinstance(result, CRS)
    assert result.to_epsg() == 4326


def test_proj4_string():
    # proj4 string as a valid input
    proj4_str = "+proj=longlat +datum=WGS84 +no_defs"
    result = ensure_crs(proj4_str)

    assert isinstance(result, CRS)
    assert result.to_epsg() == 4326


def test_wkt_string():
    # Get a WKT string as a valid input
    original_crs = CRS.from_epsg(3857)  # Web Mercator
    wkt_str = original_crs.to_wkt()

    result = ensure_crs(wkt_str)

    assert isinstance(result, CRS)
    assert result.to_epsg() == 3857


def test_different_crs_formats_equivalence():
    crs_obj = CRS.from_epsg(4326)
    crs_from_string = ensure_crs("EPSG:4326")
    crs_from_int = ensure_crs(4326)
    crs_from_obj = ensure_crs(crs_obj)

    assert crs_from_string.to_epsg() == 4326
    assert crs_from_int.to_epsg() == 4326
    assert crs_from_obj.to_epsg() == 4326
    assert crs_from_obj is crs_obj


def test_invalid_string_raises_error():
    with pytest.raises(CRSError, match="Invalid target CRS specification"):
        ensure_crs("invalid_crs_string")


def test_invalid_integer_raises_error():
    with pytest.raises(CRSError, match="Invalid target CRS specification"):
        ensure_crs(999999)  # Non-existent EPSG code


def test_none_raises_error():
    with pytest.raises(CRSError, match="Invalid target CRS specification"):
        ensure_crs(None)  # ty: ignore


def test_empty_string_raises_error():
    with pytest.raises(CRSError, match="Invalid target CRS specification"):
        ensure_crs("")


def test_performance_crs_object_reuse():
    original_crs = CRS.from_epsg(4326)

    # Multiple calls should return the same object
    result1 = ensure_crs(original_crs)
    result2 = ensure_crs(original_crs)

    assert result1 is original_crs
    assert result2 is original_crs
    assert result1 is result2


@pytest.mark.parametrize(
    "crs_input,expected_epsg",
    [
        ("EPSG:4326", 4326),
        ("epsg:4326", 4326),
        ("EPSG:3857", 3857),
        (4326, 4326),
        (3857, 3857),
        (32633, 32633),
        (2154, 2154),
    ],
)
def test_various_inputs(crs_input, expected_epsg):
    """Test various valid input formats."""
    result = ensure_crs(crs_input)

    assert isinstance(result, CRS)
    assert result.to_epsg() == expected_epsg

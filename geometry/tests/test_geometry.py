from geometry.geometry import Geometry

import pytest

from pyproj import CRS
from pyproj.exceptions import CRSError
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)
from shapely.geometry.base import BaseGeometry

geometry_types_test_data = [
    (Point(51, -1), 4326),
    (LineString([(52, -1), (49, 2)]), 4326),
    (Polygon(((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0))), 4326),
    (MultiPoint([[0, 0], [1, 2]]), 4326),
    (MultiLineString([[[0, 0], [1, 2]], [[4, 4], [5, 6]]]), 4326),
    (
        MultiPolygon(
            [
                (
                    ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)),
                    [((0.1, 0.1), (0.1, 0.2), (0.2, 0.2), (0.2, 0.1))],
                )
            ]
        ),
        4326,
    ),
    (GeometryCollection([Point(51, -1), LineString([(52, -1), (49, 2)])]), 4326),
]


@pytest.mark.parametrize(
    "geom, crs",
    geometry_types_test_data,
    ids=[
        "Point",
        "LineString",
        "Polygon",
        "MultiPoint",
        "MultiLineString",
        "MultiPolygon",
        "GeometryCollection",
    ],
)
def test_geometry_init_geometry_types(geom, crs):
    geometry = Geometry(geom, crs)

    assert geometry.geometry == geom
    assert isinstance(geometry.geometry, BaseGeometry)
    assert geometry.crs == crs
    assert isinstance(geometry.crs, CRS)


def test_geometry_init_invalid_geometry():
    with pytest.raises(TypeError, match="geometry must be a Shapely BaseGeometry"):
        Geometry("not a geometry", 4326)  # ty: ignore


geometry_crs_test_data = [
    (Point(51, -1), 4326, "4326"),
    (Point(51, -1), "EPSG:26910", "26910"),
    (Point(51, -1), CRS.from_authority("EPSG", "4326"), "4326"),
    (Point(51, -1), CRS.from_epsg(5070), "5070"),
]


@pytest.mark.parametrize(
    "geom, crs, epsg_id",
    geometry_crs_test_data,
    ids=["as int", "as epsg string", "as epsg authority", "from epsg"],
)
def test_geometry_init_crs(geom, crs, epsg_id):
    geometry = Geometry(geom, crs)

    assert geometry.crs.to_authority()[-1] == epsg_id
    assert isinstance(geometry.crs, CRS)


def test_init_invalid_crs():
    pt = Point(1, 2)
    with pytest.raises(CRSError, match="Invalid target CRS specification"):
        Geometry(pt, "invalid_crs")


# Magic methods (dunder methods) tests --------------------------------------------
def test_geometry_repr():
    geometry = Geometry(Point(1.1, 2.2), CRS.from_epsg(4326))
    assert repr(geometry) == "Geometry(geometry=<POINT (1.1 2.2)>, crs='EPSG:4326')"

    # a more complex CRS
    crs = CRS.from_proj4(
        "+proj=omerc +lat_0=-36 +lonc=147 +alpha=-54 +k=1 +x_0=0 +y_0=0 +gamma=0 +ellps=WGS84 +towgs84=0,0,0,0,0,0,0"
    )
    geometry = Geometry(Point(1.1, 2.2), crs)
    assert (
        repr(geometry)
        == "Geometry(geometry=<POINT (1.1 2.2)>, crs='+proj=omerc +lat_0=-36 +lonc=147 +alpha=-54 +k=1 +x_0=0 +y_0=0 +gamma=0 +ellps=WGS84 +towgs84=0,0,0,0,0,0,0 +type=crs')"
    )

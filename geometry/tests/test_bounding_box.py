from geometry.bounding_box import BoundingBox

import pytest
import shapely as sp

from pyproj import CRS
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

from geometry.geometry import Geometry

boundinb_box_init_params = [
    (0, 0, 1, 1, 4326),
    (1, 1, 2, 2, "EPSG:26910"),
    (-1, -1, 0, 0, "epsg:4326"),
    (0, 0, 0, 0, CRS.from_epsg(5070)),
]


@pytest.mark.parametrize(
    "minx, miny, maxx, maxy, crs",
    boundinb_box_init_params,
    ids=["EPSG:4326", "EPSG:26910", "EPSG:4326", "EPSG:5070"],
)
def test_bounding_box_init(minx, miny, maxx, maxy, crs):
    bbox = BoundingBox(minx, miny, maxx, maxy, crs)

    assert bbox.minx == minx
    assert bbox.miny == miny
    assert bbox.maxx == maxx
    assert bbox.maxy == maxy
    assert isinstance(bbox.crs, CRS)


# @staticmethod tests ---
geometry_test_data = [
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
    geometry_test_data,
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
def test_bounding_box_from_geometry(geom, crs):
    geometry = Geometry(geom, crs)
    bbox = BoundingBox.from_geometry(geometry)

    assert bbox.minx == sp.get_coordinates(geometry.geometry)[:, 0].min()
    assert bbox.miny == sp.get_coordinates(geometry.geometry)[:, 1].min()
    assert bbox.maxx == sp.get_coordinates(geometry.geometry)[:, 0].max()
    assert bbox.maxy == sp.get_coordinates(geometry.geometry)[:, 1].max()
    assert bbox.crs == geometry.crs
    assert isinstance(bbox.crs, CRS)

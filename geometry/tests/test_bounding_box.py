from geometry.bounding_box import BoundingBox

import pytest

from pyproj import CRS

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

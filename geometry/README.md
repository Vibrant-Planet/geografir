# Geometry

This package provides two classes for representing geospatial shapes: `Geometry` and `BoundingBox`.

- `Geometry` - is a wrapper around a `shapely` geometry with an added `crs` attribute.
- `BoundingBox` - the `minx`, `miny`, `maxx`, and `maxy` of a `Geometry` with a `crs`.

## Key Design Decisions

1. Minimal Wrappers: The `Geometry` class is a simple wrapper around `shapely` geometries. Users should work directly with the `Geometry.geometry` object with `shapely`'s methods and reconstruct the `Geometry` as needed.
2. Explicit CRS: Each class has an explicit, required CRS using `pyrpoj.CRS` objects.
3. Immutability: Operations return a new object rather than modifying existing objects.

## Installation

While under active development install directly from GitHub using `uv`:

```shell
# with pip
pip install git+https://github.com/Vibrant-Planet/geografir.git#subdirectory=geometry

# with uv
uv add git+https://github.com/Vibrant-Planet/geografir.git#subdirectory=geometry
```

## Basic Usage

```python
import shapely as sp
from pyproj import CRS

from geometry import Geometry

# Create geometries
point = Geometry(sp.Point(5, 5), CRS.from_epsg(26910))
#> Geometry(geometry=<POINT (5 5)>, crs='EPSG:26910')
line = Geometry(sp.LineString([(0, 0), (2, 2), (10, 10)]), "epsg:4326")
#> Geometry(geometry=<LINESTRING (0 0, 2 2, 10 10)>, crs='EPSG:4326')
polygon = Geometry(sp.Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]), crs=5070)
#> Geometry(geometry=<POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))>, crs='EPSG:5070')

# Shapely operations on the geometry
buffered_shape = sp.buffer(point.geometry, 1)
point_buffered = Geometry(buffered_shape, point.crs)
#> Geometry(geometry=<POLYGON ((6 5, 5.981 4.805, 5.924 4.617, 5.831 4.444, 5.707 4.293, 5.556 4....>, crs='EPSG:26910')

# BoundingBox
from geometry import BoundingBox
bbox = BoundingBox(0, 0, 1, 1, 5070)
#> BoundingBox(minx=0, miny=0, maxx=1, maxy=1, crs='EPSG:5070')

# from a geometry
polygon = Geometry(sp.Polygon([(0, 0), (2, 0), (1, 1), (0, 2), (0, 0)]), crs=5070)
polygon_bbox = BoundingBox.from_geometry(polygon)
#> BoundingBox(minx=0.0, miny=0.0, maxx=2.0, maxy=2.0, crs='EPSG:5070')
```

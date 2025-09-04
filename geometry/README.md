# Geometry

This package provides two classe for representing geospatial shapes: `Geometry` and `BoundingBox`.

- `Geometry` - is a wrapper around a `shapely` geometry with an added `crs` attribute.
- `BoundingBox` - the `minx`, `miny`, `maxx`, and `maxy` of a `Geometry` with a `crs`.

## Key Design Decisions

1. Minimal Wrappers: The `Geometry` class is a simple wrapper around `shapely` geometries. Users should work directly with the `Geometry.geometry` object with `shapely`'s methods and reconstruct the `Geometry` as needed.
2. Explicit CRS: Each class have an explicit, required CRS using `pyrpoj.CRS` objects.
3. Immutability: Operations return a new object rather than modifying existing objects.

## Installation

While under active development install directly from GitHub using `uv`:

```shell
uv add https://github.com/Vibrant-Planet/geografir.git#subdirectory=geometry
```

## Basic Usage

```python
import shapely as sp
from pyproj import CRS

from geometry.geometry import Geometry

# Create geometries
point = Geometry(sp.Point(5, 5), CRS.from_epsg(26910))
line = Geometry(sp.LineString([(0, 0), (2, 2), (10, 10)]), "epsg:4326")
polygon = Geometry(sp.Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]), crs=5070)

# Shapely operations on the geometry
buffered_shape = sp.buffer(point.geometry, 10)
point_buffered = Geometry(buffered_shape, point.crs)

# BoundingBox
from geometry.bounding_box import BoundingBox
polygon_bbox = BoundingBox.from_geometry(polygon)
```
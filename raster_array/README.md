# RasterArray

`RasterArray` is a wrapper around Rasterio and Numpy to make working with raster data easier.

## Installation

While under active development install directly from GitHub:

```shell
# with pip
pip install git+https://github.com/Vibrant-Planet/geografir.git#subdirectory=raster_array

# with uv
uv add git+https://github.com/Vibrant-Planet/geografir.git#subdirectory=raster_array
```

## Usage

```python
import numpy as np
import rasterio as rio

from raster_array.raster_array import RasterArray
from raster_array.raster_metadata import RasterMetadata

# create a RasterArray with a numpy array and metadata
# Metadata is very similar to a rasterio.profiles.Profile
width, height = 10, 10
metadata = RasterMetadata(
    crs=rio.CRS.from_epsg(4326),
    count=1,
    width=width,
    height=height,
    dtype=np.int16,
    nodata=-99,
    transform=rio.transform.from_bounds(0, 0, width, height, width, height),
)
data = np.arange(np.prod(metadata.shape), dtype=metadata.dtype).reshape(metadata.shape)
#> array([[[ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9],
#>        [10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
#>        [20, 21, 22, 23, 24, 25, 26, 27, 28, 29],
#>        [30, 31, 32, 33, 34, 35, 36, 37, 38, 39],
#>        [40, 41, 42, 43, 44, 45, 46, 47, 48, 49],
#>        [50, 51, 52, 53, 54, 55, 56, 57, 58, 59],
#>        [60, 61, 62, 63, 64, 65, 66, 67, 68, 69],
#>        [70, 71, 72, 73, 74, 75, 76, 77, 78, 79],
#>        [80, 81, 82, 83, 84, 85, 86, 87, 88, 89],
#>        [90, 91, 92, 93, 94, 95, 96, 97, 98, 99]]], dtype=int16)

raster = RasterArray(data, metadata)

# when creating a RasterArray the data and metadata must descripe the same reshape
# array, same dtype, and the array must be 3d
RasterArray(data[:, 0:5, 0:5], metadata)
#> RasterArrayShapeError: Array shape (1, 5, 5) does not match metadata shape (1, 10, 10)

# The most common use case is to read a raster from a file
# first, let's create a file to read
# filename = "<path/to/write.tiff"
filename="/Users/mitchellgritts/Downloads/test.tiff"
with rio.open(filename, "w", **metadata.profile) as dst:
    dst.write(data)

raster = RasterArray.from_raster(filename)

# or
with rio.open(filename, "r") as src:
    RasterArray.from_raster(src)

# let's create an array with nodata values
data[:, 0:5, 0:5] = -99
raster = RasterArray(data, metadata)

# now check the mask
raster.mask
#> array([[[ True,  True,  True,  True,  True, False, False, False, False, False],
#>         [ True,  True,  True,  True,  True, False, False, False, False, False],
#>         [ True,  True,  True,  True,  True, False, False, False, False, False],
#>         [ True,  True,  True,  True,  True, False, False, False, False, False],
#>         [ True,  True,  True,  True,  True, False, False, False, False, False],
#>         [False, False, False, False, False, False, False, False, False, False],
#>         [False, False, False, False, False, False, False, False, False, False],
#>         [False, False, False, False, False, False, False, False, False, False],
#>         [False, False, False, False, False, False, False, False, False, False]]])

# and return a MaskedArray
raster.masked
# masked_array(
#     data=[[[...]]],
#     mask=[[[...]]],
#     fill_value=-99,
#     dtype=np.int16
# )

# and a multiband raster
data = data.reshape((4, 5, 5))
# copy and modify the metadata
metadata = raster.metadata.copy(count=4, width=5, height=5)
raster = RasterArray(data, metadata)

# get band data (these always return a 3d array)
# RasterArray.band this is 1 indexed to match rasterio's implementation
raster.band(3)

# and a masked band
raster.band_masked(1)

```

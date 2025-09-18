# type: ignore
"""Tests helpers for RasterArray and RasterMetadata."""

from contextlib import contextmanager

import numpy as np
import rasterio as rio

from raster_array.profiles import apply_geotiff_profile

TAG_CLASSIFICATION_VALUES = [
    "red",
    "orange",
    "yellow",
    "green",
    "blue",
    "purple",
    "pink",
    "brown",
    "gray",
    "black",
    "white",
]
TAG_TREE_VALUES = [
    "pine",
    "maple",
    "oak",
    "birch",
    "cedar",
    "fir",
    "spruce",
    "elm",
    "ash",
    "sycamore",
    "willow",
]


@contextmanager
def generate_raster(data, nodata, dtype):
    data = data if isinstance(data, np.ndarray) else np.array(data, dtype=dtype)
    count, height, width = data.shape
    bounds = (0, 0, width, height)

    profile = apply_geotiff_profile(
        rio.profiles.Profile(
            {
                "crs": rio.CRS.from_epsg(4326),
                "count": count,
                "height": height,
                "width": width,
                "dtype": dtype,
                "nodata": nodata,
                "transform": rio.transform.from_bounds(*bounds, width, height),
            }
        )
    )

    with rio.io.MemoryFile() as memfile:
        with memfile.open(**profile) as dataset:
            dataset.write(data)
            for band in range(1, count + 1):
                tags = {"classification": TAG_CLASSIFICATION_VALUES[band - 1]}
                if band % 2 == 0:
                    tags["tree"] = TAG_TREE_VALUES[band - 1]
                dataset.update_tags(band, **tags)
        with memfile.open() as dataset:
            yield dataset

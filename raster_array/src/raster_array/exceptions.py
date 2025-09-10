class RasterArrayShapeError(Exception):
    """Used when a RasterArray is not the correct/expected shape."""


class RasterArrayDtypeError(Exception):
    """Used when a RasterArray dtype does not match the metadata dtype."""


class RasterArrayNoDataError(Exception):
    """Used when a RasterArray nodata does not match the metadata nodata value."""

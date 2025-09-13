import pytest
import numpy as np


from raster_array.band_tags import BandTags
from raster_array.raster_array import RasterArray
from raster_array.raster_test_helpers import generate_raster


@pytest.fixture(scope="session")
def raster_4_x_4_multiband():
    shape = (4, 4, 4)
    count, height, width = shape
    n = count * height * width
    array = np.arange(0, n, dtype=np.int32).reshape(shape)
    with generate_raster(array, -9999, np.int32) as dataset:
        yield dataset


def test_band_tags_init():
    band_tags_dict = {
        1: {"classification": "red", "tree": "pine"},
        2: {"classification": "green"},
        3: {"tree": "maple"},
    }
    band_tags = BandTags(band_tags_dict)

    assert band_tags.band_indices == {1, 2, 3}
    assert band_tags.tags_by_band == {
        "classification": {"red": 1, "green": 2},
        "tree": {"pine": 1, "maple": 3},
    }
    assert band_tags.count == 3
    assert band_tags.tag_names == {"classification", "tree"}
    assert band_tags_dict is not band_tags.tags


def test_band_tags_init_invalid_band_indices():
    with pytest.raises(
        ValueError, match="Band index must be a positive integer, got 0"
    ):
        BandTags({0: {"classification": "red", "tree": "pine"}})


def test_band_tags_get_band_tags():
    band_tags_dict = {
        1: {"classification": "red", "tree": "pine"},
        2: {"classification": "green"},
        3: {"tree": "maple"},
    }
    band_tags = BandTags(band_tags_dict)

    assert band_tags.get_band_tags(1) == {"classification": "red", "tree": "pine"}
    assert band_tags.get_band_tags(2) == {"classification": "green"}
    assert band_tags.get_band_tags(3) == {"tree": "maple"}
    assert band_tags.get_band_tags(99) == {}


def test_band_tags_put_band_tags():
    band_tags = BandTags({1: {"classification": "red"}})
    band_tags_1 = band_tags.put_band_tags(1, {"tree": "pine"})
    band_tags_2 = band_tags_1.put_band_tags(2, {"classification": "green"})
    band_tags_3 = band_tags_2.put_band_tags(1, {"classification": "blue"})

    assert band_tags_1.tags[1] == {"classification": "red", "tree": "pine"}
    assert band_tags_2.tags[1] == {"classification": "red", "tree": "pine"}
    assert band_tags_2.tags[2] == {"classification": "green"}
    assert band_tags_3.tags[1] == {"classification": "blue", "tree": "pine"}
    assert band_tags_3.tags[2] == {"classification": "green"}
    assert band_tags_2.tags[1] is not band_tags_3.tags[1]


def test_band_tags_write_tags(raster_4_x_4_multiband, tmp_path):
    raster = RasterArray.from_raster(raster_4_x_4_multiband)
    band_tags = BandTags(
        {
            1: {"classification": "red", "tree": "pine"},
            2: {"classification": "green"},
            3: {"tree": "maple"},
        }
    )

    tmp_raster = str(tmp_path / "test_band_tags_write_tags.tif")
    raster.to_raster(tmp_raster)
    band_tags.write_tags(tmp_raster)

    reread_band_tags = BandTags.from_raster(tmp_raster)

    assert reread_band_tags.tags[1] == {"classification": "red", "tree": "pine"}
    assert reread_band_tags.tags[2] == {"classification": "green"}
    assert reread_band_tags.tags[3] == {"tree": "maple"}


# test static methods ------------------------------------------------------------
def test_band_tags_from_raster(raster_4_x_4_multiband):
    band_tags = BandTags.from_raster(raster_4_x_4_multiband)

    print(band_tags.tags)

    assert band_tags.tags[1] == {"classification": "red"}
    assert band_tags.tags[2] == {"classification": "orange", "tree": "maple"}
    assert band_tags.tags[3] == {"classification": "yellow"}

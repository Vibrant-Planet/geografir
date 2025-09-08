from raster_array.profiles import apply_cog_profile, apply_geotiff_profile
from rasterio.profiles import Profile
from rasterio.enums import Compression


def test_apply_cog_profile():
    profile = Profile(
        {"width": 100, "height": 100, "count": 2, "tiled": True, "interleave": "band"}
    )
    with_cog_profile = apply_cog_profile(profile)

    assert with_cog_profile["driver"] == "COG"
    assert with_cog_profile["bigtiff"] == "YES"
    assert with_cog_profile["blocksize"] == 512
    assert with_cog_profile["compress"] == Compression.deflate
    assert with_cog_profile["level"] == 9
    assert with_cog_profile["overview_resampling"] == "nearest"
    assert with_cog_profile["predictor"] == "standard"
    assert "blockxsize" not in with_cog_profile
    assert "blockysize" not in with_cog_profile
    assert "tiled" not in with_cog_profile
    assert "interleave" not in with_cog_profile


def test_apply_geotiff_profile():
    profile = Profile({"width": 100, "height": 100, "count": 2, "tiled": True})
    with_geotiff_profile = apply_geotiff_profile(profile)
    assert with_geotiff_profile["driver"] == "GTiff"
    assert with_geotiff_profile["bigtiff"] == "YES"
    assert with_geotiff_profile["blockxsize"] == 512
    assert with_geotiff_profile["blockysize"] == 512
    assert with_geotiff_profile["interleave"] == "pixel"
    assert with_geotiff_profile["compress"] == Compression.deflate
    assert with_geotiff_profile["zlevel"] == 9
    assert with_geotiff_profile["tiled"]

from object_storage.object_location import S3ObjectLocation


def test_object_location():
    s3_object_location = S3ObjectLocation(
        bucket="test-bucket",
        path="test-key",
    )
    assert s3_object_location.bucket == "test-bucket"
    assert s3_object_location.path == "test-key"
    assert not s3_object_location.is_directory
    assert s3_object_location.s3_uri == "s3://test-bucket/test-key"


def test_object_location_is_directory():
    s3_object_location = S3ObjectLocation(
        bucket="test-bucket",
        path="test-key/",
    )
    assert s3_object_location.is_directory

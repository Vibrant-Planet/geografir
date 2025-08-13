from object_storage.object_location import S3ObjectLocation


def test_object_location():
    s3_object_location = S3ObjectLocation(
        bucket_name="test-bucket",
        key="test-key",
    )
    assert s3_object_location.bucket_name == "test-bucket"
    assert s3_object_location.key == "test-key"
    assert not s3_object_location.is_directory
    assert s3_object_location.s3_uri == "s3://test-bucket/test-key"


def test_object_location_is_directory():
    s3_object_location = S3ObjectLocation(
        bucket_name="test-bucket",
        key="test-key/",
    )
    assert s3_object_location.is_directory

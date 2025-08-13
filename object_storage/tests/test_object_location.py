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


def test_object_location_serialize():
    s3_object_location = S3ObjectLocation(
        bucket="test-bucket",
        path="test-key.tif",
    )
    s3_dir_location = S3ObjectLocation(
        bucket="test-bucket",
        path="test-key/",
    )
    assert s3_object_location.serialized == {
        "bucket": "test-bucket",
        "path": "test-key.tif",
    }
    assert s3_dir_location.serialized == {
        "bucket": "test-bucket",
        "path": "test-key/",
    }


def test_object_location_s3_uri():
    s3_object_location = S3ObjectLocation(
        bucket="test-bucket",
        path="test-key.tif",
    )
    assert s3_object_location.s3_uri == "s3://test-bucket/test-key.tif"

    s3_dir_location = S3ObjectLocation(
        bucket="test-bucket",
        path="test-key/",
    )
    assert s3_dir_location.s3_uri == "s3://test-bucket/test-key/"


def test_object_location_extend():
    s3_object_location = S3ObjectLocation(
        bucket="test-bucket",
        path="test-key/",
    )
    assert s3_object_location.extend("test-key.tif") == S3ObjectLocation(
        bucket="test-bucket",
        path="test-key/test-key.tif",
    )


def test_object_location_from_s3_uri():
    s3_uri = "s3://test-bucket/test-key.tif"
    assert S3ObjectLocation.from_s3_uri(s3_uri) == S3ObjectLocation(
        bucket="test-bucket",
        path="test-key.tif",
    )

    s3_uri = "s3://test-bucket/test-key/"
    assert S3ObjectLocation.from_s3_uri(s3_uri) == S3ObjectLocation(
        bucket="test-bucket",
        path="test-key/",
    )

    s3_uri = "s3://test-bucket/test-key/test-key.tif"
    assert S3ObjectLocation.from_s3_uri(s3_uri) == S3ObjectLocation(
        bucket="test-bucket",
        path="test-key/test-key.tif",
    )


def test_file_location_eq():
    dummy_file_location = S3ObjectLocation(bucket="test-bucket", path="test/dummy.txt")
    dummy_file_location_one = dummy_file_location.model_copy()
    dummy_file_location_two = S3ObjectLocation(
        bucket="test-bucket", path="test/works2.txt"
    )
    dummy_file_location_three = S3ObjectLocation(
        bucket="test-bucket", path="test/works.txt"
    )
    dummy_file_location_four = S3ObjectLocation(
        bucket="test-bucket", path="test/works2.txt"
    )
    assert dummy_file_location_one == dummy_file_location
    assert dummy_file_location_two != dummy_file_location
    assert dummy_file_location_three != dummy_file_location
    assert dummy_file_location_four != dummy_file_location


def test_file_location_hash():
    dummy_file_location = S3ObjectLocation(bucket="test-bucket", path="test/dummy.txt")
    dummy_file_location_one = dummy_file_location.model_copy()
    dummy_file_location_two = S3ObjectLocation(
        bucket="test-bucket", path="test/works2.txt"
    )
    dummy_file_location_three = S3ObjectLocation(
        bucket="test-bucket", path="test/works.txt"
    )
    dummy_file_location_four = S3ObjectLocation(
        bucket="test-bucket", path="test/works2.txt"
    )
    assert hash(dummy_file_location_one) == hash(dummy_file_location)
    assert hash(dummy_file_location_two) != hash(dummy_file_location)
    assert hash(dummy_file_location_three) != hash(dummy_file_location)
    assert hash(dummy_file_location_four) != hash(dummy_file_location)

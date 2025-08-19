import os
import pytest
import boto3
from moto import mock_aws
from tempfile import TemporaryDirectory

from object_storage.object_store import ObjectStore
from object_storage.object_location import ObjectLocation

TEST_BUCKET = "test_bucket"


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-west-2"


@pytest.fixture(scope="function")
def s3(aws_credentials):
    """
    Return a mocked S3 client
    """
    with mock_aws():
        yield boto3.client("s3", region_name="us-east-1")


def create_files(s3):
    s3.create_bucket(Bucket=TEST_BUCKET)
    s3.put_object(Bucket=TEST_BUCKET, Key="path/one.txt", Body="test1")
    s3.put_object(Bucket=TEST_BUCKET, Key="path/two.txt", Body="test2")


def test_list_files(s3):
    create_files(s3)
    store = ObjectStore(s3_client=s3)

    object_location = ObjectLocation(bucket=TEST_BUCKET, path="path/")
    files = store.list_files(object_location)

    assert files == [
        ObjectLocation(bucket=TEST_BUCKET, path="path/one.txt"),
        ObjectLocation(bucket=TEST_BUCKET, path="path/two.txt"),
    ]


def test_download_file(s3):
    create_files(s3)
    store = ObjectStore(s3_client=s3)

    object_location = ObjectLocation(bucket=TEST_BUCKET, path="path/one.txt")

    with TemporaryDirectory() as tmpdir:
        local_filename = store.download_file(
            object_location=object_location,
            local_directory=tmpdir,
        )
        assert local_filename == os.path.join(tmpdir, "one.txt")
        assert os.path.exists(local_filename)
        with open(local_filename) as f:
            assert f.read() == "test1"


def test_download_file_with_local_name_override(s3):
    create_files(s3)
    store = ObjectStore(s3_client=s3)

    object_location = ObjectLocation(bucket=TEST_BUCKET, path="path/one.txt")

    with TemporaryDirectory() as tmpdir:
        local_filename = store.download_file(
            object_location=object_location,
            local_directory=tmpdir,
            local_filename="override.txt",
        )
        assert local_filename == os.path.join(tmpdir, "override.txt")
        assert os.path.exists(local_filename)
        with open(local_filename) as f:
            assert f.read() == "test1"


def test_download_directory(s3):
    create_files(s3)
    store = ObjectStore(s3_client=s3)

    object_location = ObjectLocation(bucket=TEST_BUCKET, path="path/")

    with TemporaryDirectory() as tmpdir:
        local_filenames = store.download_directory(
            object_location=object_location,
            local_directory=tmpdir,
        )
        assert len(local_filenames) == 2

        assert os.path.exists(os.path.join(tmpdir, "one.txt"))
        assert os.path.exists(os.path.join(tmpdir, "two.txt"))


def test_upload_file(s3):
    create_files(s3)
    store = ObjectStore(s3_client=s3)

    upload_location = ObjectLocation(bucket=TEST_BUCKET, path="uploads/")
    object_location = upload_location.extend("upload.txt")

    with TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "upload.txt")
        with open(filepath, "w") as f:
            f.write("upload me!")

        store.upload_file(
            object_location=object_location,
            local_filepath=filepath,
        )

    with TemporaryDirectory() as tmpdir:
        local_filename = store.download_file(
            object_location=object_location,
            local_directory=tmpdir,
        )
        assert local_filename == os.path.join(tmpdir, "upload.txt")
        assert os.path.exists(local_filename)
        with open(local_filename) as f:
            assert f.read() == "upload me!"


def test_upload_directory(s3):
    create_files(s3)
    store = ObjectStore(s3_client=s3)

    upload_location = ObjectLocation(bucket=TEST_BUCKET, path="uploads/")

    with TemporaryDirectory() as tmpdir:
        for i in range(2):
            filepath = os.path.join(tmpdir, f"upload{i}.txt")
            with open(filepath, "w") as f:
                f.write("upload me!")

        store.upload_directory(
            object_location=upload_location,
            local_directory=tmpdir,
        )

    with TemporaryDirectory() as tmpdir:
        local_filenames = store.download_directory(
            object_location=upload_location,
            local_directory=tmpdir,
        )
        for i in range(2):
            local_filename = os.path.join(tmpdir, f"upload{i}.txt")
            assert local_filename in local_filenames


def test_remote_file_exists(s3):
    create_files(s3)
    store = ObjectStore(s3_client=s3)

    existing_location = ObjectLocation(bucket=TEST_BUCKET, path="path/one.txt")
    assert store.remote_file_exists(existing_location)

    non_existing_location = ObjectLocation(bucket=TEST_BUCKET, path="path/three.txt")
    assert not store.remote_file_exists(non_existing_location)

    prefix_location = ObjectLocation(bucket=TEST_BUCKET, path="path")
    assert store.remote_file_exists(prefix_location)

    directory_location = ObjectLocation(bucket=TEST_BUCKET, path="path/")
    assert store.remote_file_exists(directory_location)


def test_copy_remote_file(s3):
    create_files(s3)
    store = ObjectStore(s3_client=s3)

    src = ObjectLocation(bucket=TEST_BUCKET, path="path/one.txt")
    dst = ObjectLocation(bucket=TEST_BUCKET, path="path/three.txt")
    store.copy_remote_file(src, dst)

    # Check that the source file still exists
    assert store.remote_file_exists(src)

    # Check that the destination file exists and is correct
    assert store.remote_file_exists(dst)
    with TemporaryDirectory() as tmpdir:
        local_filename = store.download_file(
            object_location=dst,
            local_directory=tmpdir,
        )
        assert local_filename == os.path.join(tmpdir, "three.txt")
        with open(local_filename) as f:
            assert f.read() == "test1"


def test_copy_remote_directory(s3):
    create_files(s3)
    store = ObjectStore(s3_client=s3)

    src = ObjectLocation(bucket=TEST_BUCKET, path="path/")
    dst = ObjectLocation(bucket=TEST_BUCKET, path="dst_path/")
    store.copy_remote_directory(src, dst)

    # Check that the destination directory exists and contains correct files
    assert store.remote_file_exists(dst)
    with TemporaryDirectory() as tmpdir:
        local_filenames = store.download_directory(
            object_location=dst,
            local_directory=tmpdir,
        )
        assert len(local_filenames) == 2
        for filename in ["one.txt", "two.txt"]:
            assert os.path.join(tmpdir, filename) in local_filenames

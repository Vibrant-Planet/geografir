import os
import pytest
import boto3
from moto import mock_aws

from object_storage.storage_helpers import ObjectStoreClient
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
    s3.put_object(Bucket=TEST_BUCKET, Key="/path/one.txt", Body="test1")
    s3.put_object(Bucket=TEST_BUCKET, Key="/path/two.txt", Body="test2")


def test_list_files(s3):
    create_files(s3)
    client = ObjectStoreClient(s3_client=s3)

    object_location = ObjectLocation(bucket=TEST_BUCKET, path="/path/")
    files = client.list_files(object_location)

    assert files == [
        ObjectLocation(bucket=TEST_BUCKET, path="/path/one.txt"),
        ObjectLocation(bucket=TEST_BUCKET, path="/path/two.txt"),
    ]


def test_download_file(s3):
    create_files(s3)
    client = ObjectStoreClient(s3_client=s3)

    object_location = ObjectLocation(bucket=TEST_BUCKET, path="/path/one.txt")

    local_filename = client.download_file(
        object_location=object_location,
        local_directory="/tmp",
    )
    assert local_filename == "/tmp/one.txt"
    assert os.path.exists(local_filename)
    with open(local_filename) as f:
        assert f.read() == "test1"
    os.remove(local_filename)


def test_download_file_with_local_name_override(s3):
    create_files(s3)
    client = ObjectStoreClient(s3_client=s3)

    object_location = ObjectLocation(bucket=TEST_BUCKET, path="/path/one.txt")

    local_filename = client.download_file(
        object_location=object_location,
        local_directory="/tmp",
        local_filename="override.txt",
    )
    assert local_filename == "/tmp/override.txt"
    assert os.path.exists(local_filename)
    with open(local_filename) as f:
        assert f.read() == "test1"
    os.remove(local_filename)

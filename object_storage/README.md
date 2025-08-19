# S3 Object Storage

Helpers for interacting with objects stored on S3. This package is specific to S3, we do not guarantee compatibility with other object storage services.

## Installation

While under active development install directly from GitHub:

```
uv add https://github.com/Vibrant-Planet/geografir.git#subdirectory=object_storage                 1.543s
```

## Usage

There are two main use cases for this package:

1. Identify objects stored in S3 with `ObjectLocation`
2. Interact with these objects with `ObjectStore`

```python
import boto3
from geografir.object_storage import ObjectLocation, ObjectStore

# Identify objects stored in S3 with ObjectLocation
dir_location = ObjectLocation(bucket="my-bucket", path="dir")
file_location = ObjectLocation(bucket="my-bucket", path="dir/object-1.json")

# Interact with these objects with ObjectStore
s3_client = boto3.client('s3')
store = ObjectStore(s3_client=s3_client)

# upload a file
store.upload_file(file_location, "/tmp/object-1.json")

# download a file
store.download_file(file_location, "/tmp", "object-1-downloaded.json")

# list files
store.list_files(dir_location)
```

from __future__ import annotations

import json

from urllib.parse import urlparse

from pydantic import BaseModel


# TODO: do we want any validator methods?
class S3ObjectLocation(BaseModel):
    """Location in an cloud object store.

    Args:
        bucket (str): the top level folder/directory/bucket of the object.
        path (str): the remaining information to identify the object.
    """

    bucket: str
    path: str

    @property
    def is_directory(self):
        return self.path.endswith("/")

    @property
    def serialized(self) -> dict:
        """Serialized representation of S3ObjectLocation."""
        return json.loads(self.model_dump_json())

    @property
    def s3_uri(self) -> str:
        """Get an S3 URI of the S3ObjectLocation"""
        return f"s3://{self.bucket}/{self.path}"

    def extend(self, new_part: str) -> S3ObjectLocation:
        """Extend the path of an existing S3ObjectLocation to make a new S3ObjectLocation.

        Args:
            new_part (str): a string to add to the end of `S3ObjectLocation.path`

        Returns:
            S3ObjectLocation
        """
        path = self.path[:-1] if self.path.endswith("/") else self.path
        path_extension = new_part[1:] if new_part.startswith("/") else new_part

        return S3ObjectLocation(bucket=self.bucket, path=f"{path}/{path_extension}")

    @staticmethod
    def from_s3_uri(s3_uri: str) -> S3ObjectLocation:
        """Get an S3 URI that points to an S3ObjectLocation.

        Args:
            s3_uri (str): an S3 URI string to parse into an S3ObjectLocation.

        Raises:
            ValueError: If s3_uri path contains `//` in its path portion.

        Returns:
            S3ObjectLocation: for the given S3 URI.
        """
        parsed = urlparse(s3_uri)

        if parsed.scheme != "s3":
            msg = "Argument to S3ObjectLocation.from_s3_uri must begin with 's3'"
            raise Exception(msg)

        if "//" in parsed.path:
            msg = "s3_uri contains `//` in its path portion, which is not supported."
            raise ValueError(msg)

        return S3ObjectLocation(
            bucket=parsed.netloc,
            path=parsed.path[1:],
        )

    # __dunder methods__
    def __eq__(self, other: object) -> bool:
        if isinstance(other, S3ObjectLocation):
            return other.bucket == self.bucket and other.path == self.path
        return False

    def __hash__(self):
        return hash((self.bucket, self.path))

    def __str__(self) -> str:
        return self.s3_uri

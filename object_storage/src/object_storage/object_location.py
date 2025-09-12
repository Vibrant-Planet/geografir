"""Cloud object storage location management for S3-compatible storage systems.

This module provides the ObjectLocation class for representing and manipulating
paths to objects stored in cloud object storage systems. The implementation focuses
on S3-compatible storage with bucket and path semantics, offering utilities for
URI parsing, path manipulation, and location-based operations.

Classes:
    ObjectLocation: A Pydantic model representing cloud object storage locations
        with bucket and path components. Provides methods for URI conversion,
        path manipulation, and location-based operations with validation and
        type safety through Pydantic's model framework.

Examples:
    Basic object location creation and manipulation:

    >>> # Create object location directly
    >>> location = ObjectLocation(bucket="my-bucket", path="data/file.txt")
    >>> print(location.s3_uri)
    s3://my-bucket/data/file.txt

    >>> # Parse from S3 URI
    >>> uri_location = ObjectLocation.from_s3_uri("s3://bucket/path/to/object.json")
    >>> print(f"Bucket: {uri_location.bucket}, Path: {uri_location.path}")
    Bucket: bucket, Path: path/to/object.json

    Working with directory paths and extensions:

    >>> # Directory location
    >>> dir_location = ObjectLocation(bucket="data-lake", path="datasets/")
    >>> print(f"Is directory: {dir_location.is_directory}")
    Is directory: True

    >>> # Extend path to create new location
    >>> file_location = dir_location.extend("processed/results.csv")
    >>> print(file_location.s3_uri)
    s3://data-lake/datasets/processed/results.csv

Warning:
    The module currently focuses on S3. While the design allows for future
    extension to other cloud storage backends, current implementations assume
    S3 URI schemes and path semantics.
"""

from __future__ import annotations


from urllib.parse import urlparse

from pydantic import BaseModel


# TODO: do we want any validator methods?
class ObjectLocation(BaseModel):
    """Represents a location in cloud object storage with bucket and path components.

    ObjectLocation serves as a type-safe abstraction for cloud storage references,
    enabling consistent handling of object locations across different storage operations.

    Attributes:
        bucket (str): The top-level container, bucket, or namespace identifier in the
            cloud storage system.
        path (str): The object-specific path within the bucket that uniquely identifies
            the storage location. Follows filesystem-like semantics with forward slash
            separators.
    """

    bucket: str
    path: str

    @property
    def is_directory(self):
        """Check if the object location represents a directory path.

        Returns:
            bool: True if the path ends with a forward slash, indicating a directory
                location. False for file objects or paths without trailing slashes.

        Examples:
            Distinguish between files and directories:

            >>> file_location = ObjectLocation(bucket="data", path="file.txt")
            >>> print(file_location.is_directory)
            False

            >>> dir_location = ObjectLocation(bucket="data", path="folder/")
            >>> print(dir_location.is_directory)
            True

            >>> root_location = ObjectLocation(bucket="data", path="")
            >>> print(root_location.is_directory)
            False
        """
        return self.path.endswith("/")

    @property
    def s3_uri(self) -> str:
        """Generate an S3 URI representation of the object location.

        Creates a standardized S3 URI string that fully specifies the object location
        using the s3:// scheme.

        Returns:
            str: A complete S3 URI in the format "s3://bucket/path" that uniquely
                identifies the object location.

        Examples:
            Generate S3 URIs for different object types:

            >>> file_obj = ObjectLocation(bucket="documents", path="report.pdf")
            >>> print(file_obj.s3_uri)
            s3://documents/report.pdf

            >>> nested_obj = ObjectLocation(bucket="logs", path="2024/01/app.log")
            >>> print(nested_obj.s3_uri)
            s3://logs/2024/01/app.log

            >>> dir_obj = ObjectLocation(bucket="backup", path="daily/")
            >>> print(dir_obj.s3_uri)
            s3://backup/daily/

            Use with cloud storage tools:

            >>> location = ObjectLocation(bucket="data-lake", path="datasets/sales.csv")
            >>> uri = location.s3_uri
            >>> # URI can be used with AWS CLI: aws s3 cp {uri} local/path
        """
        return f"s3://{self.bucket}/{self.path}"

    def extend(self, new_part: str) -> ObjectLocation:
        """Create a new ObjectLocation by extending the current path.

        Constructs a new ObjectLocation instance with an extended path by appending
        the specified path component.

        Args:
            new_part (str): The path component to append to the current object path.

        Returns:
            ObjectLocation: A new ObjectLocation instance with the same bucket and
                an extended path created by properly joining the current path with
                the new component.

        Examples:
            Extend paths to create nested locations:

            >>> base = ObjectLocation(bucket="storage", path="data")
            >>> extended = base.extend("processed/results.json")
            >>> print(extended.s3_uri)
            s3://storage/data/processed/results.json

            Handle directory paths with trailing slashes:

            >>> dir_base = ObjectLocation(bucket="archive", path="2024/")
            >>> monthly = dir_base.extend("january/reports.zip")
            >>> print(monthly.s3_uri)
            s3://archive/2024/january/reports.zip

            Chain multiple extensions:

            >>> start = ObjectLocation(bucket="project", path="src")
            >>> middle = start.extend("components")
            >>> final = middle.extend("utils/helper.py")
            >>> print(final.s3_uri)
            s3://project/src/components/utils/helper.py
        """
        path = self.path[:-1] if self.path.endswith("/") else self.path
        path_extension = new_part[1:] if new_part.startswith("/") else new_part

        return ObjectLocation(bucket=self.bucket, path=f"{path}/{path_extension}")

    @staticmethod
    def from_s3_uri(s3_uri: str) -> ObjectLocation:
        """Parse an S3 URI string into an ObjectLocation instance.

        Converts a stamdard S3 URI into structured ObjectLocation components
        by parsing the URI scheme, bucket, and path elements.

        Args:
            s3_uri (str): A complete S3 URI string following the format
                "s3://bucket/path". The URI must use the "s3" scheme.

        Returns:
            ObjectLocation: A new ObjectLocation instance with bucket and path
                components extracted from the parsed URI.

        Raises:
            Exception: Raised when the URI does not use the "s3" scheme.
            ValueError: Raised when the URI path contains consecutive forward
                slashes ("//") which are not supported by the ObjectLocation
                model.

        Examples:
            Parse various S3 URI formats:

            >>> nested = ObjectLocation.from_s3_uri("s3://analytics/reports/2024/q1.json")
            >>> print(nested.s3_uri)
            s3://analytics/reports/2024/q1.json

            >>> # Directory URI with trailing slash
            >>> directory = ObjectLocation.from_s3_uri("s3://backup/daily/")
            >>> print(f"Is directory: {directory.is_directory}")
            Is directory: True
        """
        parsed = urlparse(s3_uri)

        if parsed.scheme != "s3":
            msg = "Argument to ObjectLocation.from_s3_uri must begin with 's3'"
            raise Exception(msg)

        if "//" in parsed.path:
            msg = "s3_uri contains `//` in its path portion, which is not supported."
            raise ValueError(msg)

        return ObjectLocation(
            bucket=parsed.netloc,
            path=parsed.path[1:],
        )

    # __dunder methods__
    def __eq__(self, other: object) -> bool:
        """Test equality between ObjectLocation instances."""
        if isinstance(other, ObjectLocation):
            return other.bucket == self.bucket and other.path == self.path
        return False

    def __hash__(self):
        """Generate a hash value for the ObjectLocation instance."""
        return hash((self.bucket, self.path))

    def __str__(self) -> str:
        """Return the S3 URI string representation of the ObjectLocation."""
        return self.s3_uri

"""S3-compatible object storage operations with high-level file and directory management.

This module provides the ObjectStore class for performing common object storage
operations against S3-compatible storage systems. The implementation wraps boto3
client functionality with simplified interfaces for file transfers, directory
operations, and remote file management while handling pagination, error conditions,
and requester-pays scenarios.

Classes:
    ObjectStore: High-level wrapper around S3 client functionality providing
        simplified interfaces for object operations.

Examples:
    Basic file operations with S3 storage:

    >>> import boto3
    >>> from object_storage import ObjectStore, ObjectLocation
    >>>
    >>> # Initialize with S3 client
    >>> s3_client = boto3.client('s3')
    >>> store = ObjectStore(s3_client)
    >>>
    >>> # Upload and download files
    >>> location = ObjectLocation(bucket="my-bucket", path="data/file.txt")
    >>> store.upload_file(location, "local_file.txt")
    >>> store.download_file(location, "/tmp", "downloaded.txt")

    Directory operations and bulk transfers:

    >>> # List all files in a directory
    >>> dir_location = ObjectLocation(bucket="data-lake", path="datasets/")
    >>> files = store.list_files(dir_location)
    >>> print(f"Found {len(files)} files")
    >>>
    >>> # Download entire directory
    >>> local_files = store.download_directory(dir_location, "/local/data")
    >>>
    >>> # Upload local directory to S3
    >>> upload_location = ObjectLocation(bucket="backup", path="daily/")
    >>> store.upload_directory(upload_location, "/local/backup")
"""

from __future__ import annotations

import logging
import os

from botocore.client import BaseClient

from object_storage.object_location import ObjectLocation


class ObjectStore:
    """High-level interface for S3-compatible object storage operations.

    ObjectStore provides a simplified wrapper around boto3 S3 client functionality,
    offering intuitive methods for common storage operations

    Attributes:
        _s3_client (BaseClient): The underlying boto3 S3 client instance used for
            all storage operations. Handles authentication, region configuration,
            and low-level API communications.
        _requester_pays (bool): Flag indicating whether storage operations should
            include requester-pays billing instructions. When True, all API calls
            include appropriate parameters to indicate the requesting party will
            accept charges for data transfer and request costs, enabling access
            to requester-pays enabled buckets.
    """

    _s3_client: BaseClient
    _requester_pays: bool

    def __init__(self, s3_client: BaseClient, requester_pays: bool = False):
        self._s3_client = s3_client
        self._requester_pays = requester_pays

    def list_files(
        self,
        object_location: ObjectLocation,
    ) -> list[ObjectLocation]:
        """List all files at the specified S3 location with automatic pagination.

        Retrieves a complete list of all objects at the given location by handling
        S3's pagination automatically.

        Args:
            object_location (ObjectLocation): The S3 directory location to list.

        Returns:
            list[ObjectLocation]: A complete list of ObjectLocation instances representing
                all objects found at the specified location.

        Examples:
            List files in a directory:

            >>> from object_storage.object_location import ObjectLocation
            >>> dir_location = ObjectLocation(bucket="data", path="reports/2024/")
            >>> files = store.list_files(dir_location)
            >>> for file_loc in files:
            ...     print(file_loc.s3_uri)
            s3://data/reports/2024/january.csv
            s3://data/reports/2024/february.csv
        """
        continuation_token = None
        should_continue = True
        keys = []

        while should_continue:
            extra_params: dict[str, str | None] = (
                {"ContinuationToken": continuation_token}
                if continuation_token is not None
                else {}
            )

            s3_result = self._s3_client.list_objects_v2(
                Bucket=object_location.bucket,
                Prefix=object_location.path,
                RequestPayer="requester" if self._requester_pays else "owner",
                **extra_params,
            )
            if "Contents" in s3_result:
                keys.extend(
                    [
                        ObjectLocation(bucket=object_location.bucket, path=x["Key"])
                        for x in s3_result["Contents"]
                    ]
                )
            should_continue = s3_result["IsTruncated"]
            if should_continue:
                continuation_token = s3_result["NextContinuationToken"]
        return keys

    def download_file(
        self,
        object_location: ObjectLocation,
        local_directory: str,
        local_filename: str | None = None,
    ) -> str:
        """Download a single file from S3 to a local directory.

        Transfers the specified S3 object to the local filesystem with configurable
        destination naming.

        Args:
            object_location (ObjectLocation): The S3 object to download, containing
                both the bucket identifier and the complete object path within that
                bucket. The path must reference a specific file object rather than
                a directory prefix.
            local_directory (str): The local filesystem directory where the downloaded
                file will be stored. The directory must exist and be writable by the
                current process.
            local_filename (str | None, optional): The desired filename for the
                downloaded file within the local directory. If None, the basename
                of the S3 object path will be used as the local filename. This
                allows for file renaming during download or resolving filename
                conflicts in the destination directory.

        Returns:
            str: The complete local filesystem path to the downloaded file.

        Examples:
            Download with automatic filename:

            >>> location = ObjectLocation(bucket="data", path="reports/quarterly.pdf")
            >>> local_path = store.download_file(location, "/tmp")
            >>> print(f"Downloaded to: {local_path}")
            Downloaded to: /tmp/quarterly.pdf

            Download with custom filename:

            >>> renamed_path = store.download_file(location, "/downloads", "q1_report.pdf")
            >>> print(f"Renamed file: {renamed_path}")
            Renamed file: /downloads/q1_report.pdf
        """
        if not local_filename:
            local_filename = os.path.basename(object_location.path)
        download_path = os.path.join(local_directory, local_filename)

        self._s3_client.download_file(
            Bucket=object_location.bucket,
            Key=object_location.path,
            Filename=download_path,
            ExtraArgs={"RequestPayer": "requester"} if self._requester_pays else {},
        )

        logging.debug(
            f"Downloaded {object_location.bucket}:{object_location.path} to {download_path}"
        )
        return download_path

    def download_directory(
        self,
        object_location: ObjectLocation,
        local_directory: str,
    ) -> list[str]:
        """Download all files from an S3 directory to a local directory.

        Performs bulk download of all objects matching the specified location prefix,
        effectively downloading an entire S3 "directory" to the local filesystem.
        This method combines object listing and individual file downloads to provide
        complete directory synchronization functionality.

        Args:
            object_location (ObjectLocation): The S3 directory location to download.
            local_directory (str): The destination directory on the local filesystem
                where all downloaded files will be stored. The directory must exist
                and have sufficient space for all files being downloaded. File naming
                follows the basename of each S3 object path.

        Returns:
            list[str]: A list of local filesystem paths for all successfully downloaded
                files. Each path represents a file that was transferred from S3 to
                the local directory.

        Raises:
            Exception: Any download failure for individual files will propagate as
                an exception, halting the directory download operation. Files that
                were successfully downloaded before the failure remain on the local
                filesystem without automatic cleanup. Callers requiring transactional
                behavior should use temporary directories for atomic operations.

        Examples:
            Download entire directory:

            >>> dir_location = ObjectLocation(bucket="backup", path="daily/")
            >>> downloaded_files = store.download_directory(dir_location, "/restore")
            >>> print(f"Downloaded {len(downloaded_files)} files to /restore")

            Download with prefix matching:

            >>> log_location = ObjectLocation(bucket="logs", path="app-2024")
            >>> log_files = store.download_directory(log_location, "/var/log")
        """

        remote_locations = self.list_files(object_location=object_location)

        local_filepaths = [
            self.download_file(
                object_location=object_location,
                local_directory=local_directory,
            )
            for object_location in remote_locations
        ]
        logging.debug(f"Downloaded {len(local_filepaths)} files in {local_directory}")
        return local_filepaths

    def upload_file(
        self,
        object_location: ObjectLocation,
        local_filepath: str,
    ) -> None:
        """Upload a local file to the specified S3 location.

        Args:
            object_location (ObjectLocation): The destination S3 location where the
                file will be stored.
            local_filepath (str): The complete path to the local file to upload.
                Must reference an existing, readable file on the local filesystem.
                The file content will be transferred exactly as stored locally
                without modification or encoding changes.

        Raises:
            ValueError: Raised when the specified local file does not exist or
                cannot be accessed.

        Examples:
            Upload file to S3:

            >>> location = ObjectLocation(bucket="data", path="uploads/document.pdf")
            >>> store.upload_file(location, "/local/files/document.pdf")

            Upload with different S3 name:

            >>> renamed_location = ObjectLocation(bucket="backup", path="daily/backup.tar.gz")
            >>> store.upload_file(renamed_location, "/tmp/system_backup.tar.gz")
        """
        if not os.path.exists(local_filepath):
            msg = f"File not found: {local_filepath}."
            raise ValueError(msg)

        self._s3_client.upload_file(
            Filename=local_filepath,
            Bucket=object_location.bucket,
            Key=object_location.path,
        )
        logging.debug(f"Uploaded {local_filepath} to {object_location}")

    def upload_directory(
        self,
        object_location: ObjectLocation,
        local_directory: str,
        recursive: bool = False,
    ) -> None:
        """Upload all files from a local directory to S3.

        Performs bulk upload of all files in the specified local directory to S3
        storage, creating individual S3 objects for each local file. The directory
        structure of the local directory will be preserved in S3. File names
        will be the same, and subdirectories will be preserved.

        Args:
            object_location (ObjectLocation): The base S3 location for uploaded files.
                Individual files will be stored with paths created by extending this
                base location with each local filename.
            local_directory (str): The local directory containing files to upload.
                If recursive=False, only immediate directory contents are processed.
                If recursive=True, all subdirectories are traversed and the directory
                structure is preserved in S3.
            recursive (bool, optional): If True crawl the local directory and upload
                all files from any subdirectories. The directory structure will be
                preserved in S3. Defaults to False.

        Examples:
            Upload directory contents:

            >>> base_location = ObjectLocation(bucket="backup", path="daily/")
            >>> store.upload_directory(base_location, "/local/backup")
            >>> # Uploads /local/backup/file1.txt to s3://backup/daily/file1.txt
            >>> # Uploads /local/backup/file2.txt to s3://backup/daily/file2.txt
        """
        # When topdown=True the the tuple for the diretory is generated before
        # its subdirectories. This means local_directory is always first
        directory_tree = list(os.walk(local_directory, topdown=True))
        directory_tree = directory_tree if recursive else directory_tree[:1]

        for root, _dirs, files in directory_tree:
            for file in files:
                local_path = os.path.join(root, file)
                relative_path = str(os.path.relpath(local_path, local_directory))
                s3_location = object_location.extend(relative_path)

                self.upload_file(s3_location, local_path)

    def remote_file_exists(
        self,
        object_location: ObjectLocation,
    ) -> bool:
        """Check if an object exists at the specified S3 location.

        Args:
            object_location (ObjectLocation): The S3 location to check for object
                existence.

        Returns:
            bool: True if the object exist the specified location. False if no
                objects match the location.

        Examples:
            Check specific file existence:

            >>> file_location = ObjectLocation(bucket="data", path="reports/q1.pdf")
            >>> exists = store.remote_file_exists(file_location)
            >>> print(f"File exists: {exists}")

            Check directory existence:

            >>> dir_location = ObjectLocation(bucket="data", path="reports/")
            >>> has_reports = store.remote_file_exists(dir_location)
            >>> print(f"Reports directory has files: {has_reports}")

        Note:
            The method uses S3's list_objects_v2 operation with MaxKeys=1 for
            efficient existence checking without transferring object metadata
            or content.
        """
        response = self._s3_client.list_objects_v2(
            Bucket=object_location.bucket, Prefix=object_location.path, MaxKeys=1
        )

        # If 'Contents' is in the response, it means objects with that prefix exist.
        return "Contents" in response

    def copy_remote_file(
        self,
        src_object_location: ObjectLocation,
        dst_object_location: ObjectLocation,
    ) -> None:
        """Copy a file from one S3 location to another.

        Performs server-side copying of an S3 object without downloading and
        re-uploading the content.

        Args:
            src_object_location (ObjectLocation): The source S3 location containing
                the file to copy. Must reference an existing object that is accessible
                with the current credentials and permissions.
            dst_object_location (ObjectLocation): The destination S3 location where
                the copied file will be stored. Can be in the same bucket or a
                different bucket, and may use any desired object path for the copy.

        Examples:
            Copy file within same bucket:

            >>> src = ObjectLocation(bucket="data", path="original/file.txt")
            >>> dst = ObjectLocation(bucket="data", path="backup/file.txt")
            >>> store.copy_remote_file(src, dst)

            Copy file across buckets:

            >>> src_bucket = ObjectLocation(bucket="source", path="data.csv")
            >>> dst_bucket = ObjectLocation(bucket="destination", path="imported.csv")
            >>> store.copy_remote_file(src_bucket, dst_bucket)
        """
        logging.debug(f"Copying {src_object_location} to {dst_object_location}")
        self._s3_client.copy(
            {
                "Bucket": src_object_location.bucket,
                "Key": src_object_location.path,
            },
            dst_object_location.bucket,
            dst_object_location.path,
        )

    def copy_remote_directory(
        self,
        src_object_location: ObjectLocation,
        dst_object_location: ObjectLocation,
    ) -> None:
        """Copy all files from one S3 directory to another.

        Performs bulk copying of all objects matching the source location to the
        destination location, effectively copying an entire S3 "directory" to a
        new location.

        Args:
            src_object_location (ObjectLocation): The source S3 directory location
                to copy from. All objects in this location  will be included in the
                copy operation.
            dst_object_location (ObjectLocation): The destination S3 directory
                location where copied files will be stored. Files maintain their
                original basenames but are placed under this new location.

        Examples:
            Copy directory within bucket:

            >>> src_dir = ObjectLocation(bucket="data", path="2023/")
            >>> dst_dir = ObjectLocation(bucket="data", path="archive/2023/")
            >>> store.copy_remote_directory(src_dir, dst_dir)

            Copy directory across buckets:

            >>> src_backup = ObjectLocation(bucket="daily", path="backup/")
            >>> dst_archive = ObjectLocation(bucket="longterm", path="daily/")
            >>> store.copy_remote_directory(src_backup, dst_archive)
        """
        logging.debug(f"Copying {src_object_location} to {dst_object_location}")

        src_locations = self.list_files(src_object_location)

        for src_location in src_locations:
            dst_location = dst_object_location.extend(
                os.path.basename(src_location.path)
            )

            self.copy_remote_file(src_location, dst_location)

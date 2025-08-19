from __future__ import annotations

import logging
import os

from botocore.client import BaseClient

from object_storage.object_location import ObjectLocation


class ObjectStore:
    """Wrapper class for client and other info that is common to all object store calls.

    Args:
        _s3_client (BaseClient): client to be used
        _requester_pays (bool): whether a "requester pays" instruction should be
            injected into calls using this client.
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
        """List all the files in an S3 ObjectLocation.

        Args:
            object_location(ObjectLocation): the bucket and path to read from

        Returns:
            List[ObjectLocation]: a list of all the files in the provided location
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
        """Download a single file from a S3 bucket.

        Args:
            object_location (ObjectLocation): Object containing s3 bucket and full s3 file path
            local_directory (str): a destination directory for the file
            local_filename(str): an optional destination filename for the file. If not provided, uses the location path's basename

        Returns:
            the local path to the file that was downloaded
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
        """Download all files from a S3 bucket that begin with a given key prefix.

        (i.e. a "folder" full of files that may vary.)

        Args:
            object_location (ObjectLocation): s3 bucket and full s3 file path
            local_directory (str): a destination directory for the files

        Returns:
            List of all files that were downloaded.

        Raises:
            If any of files fails to download.
                There is no attempt at cleanup of files that were downloaded prior to the failure.
                If the caller needs cleanup, it should pass in a TemporaryDirectory.
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
        """Uploads file to s3.

        Args:
            object_location (ObjectLocation): destination s3 bucket and full s3 file path
            local_filename (str): source file to upload

        Raises:
            ValueError if local_filename does not exist
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
    ) -> None:
        """Uploads all files from a local directory to s3. Directories with subdirectories are not supported.

        Args:
            object_location (ObjectLocation): s3 bucket and full s3 file path
            local_directory (str): a destination directory for the files

        Returns:
            List of all local file names that were uploaded.
        """
        filenames = os.listdir(local_directory)

        for filename in filenames:
            local_filepath = os.path.join(local_directory, filename)
            remote_location = object_location.extend(filename)

            self.upload_file(
                object_location=remote_location,
                local_filepath=local_filepath,
            )

    def remote_file_exists(
        self,
        object_location: ObjectLocation,
    ) -> bool:
        """Return True if the object_location exists in S3.

        Args:
            object_location (ObjectLocation): s3 bucket and full s3 file path
        """
        # list_objects with a max keys of 1 will check for both complete
        # and incomplete (directory/prefix) paths
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
        """Copies a file from one s3 location to another.

        Args:
            src_object_location(ObjectLocation): source location
            dst_object_location(ObjectLocation): destination location
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
        """Copies all files in one directory to another directory.

        Args:
            src_object_location(ObjectLocation): source location
            dst_object_location(ObjectLocation): destination location
        """
        logging.debug(f"Copying {src_object_location} to {dst_object_location}")

        src_locations = self.list_files(src_object_location)

        for src_location in src_locations:
            dst_location = dst_object_location.extend(
                os.path.basename(src_location.path)
            )

            self.copy_remote_file(src_location, dst_location)

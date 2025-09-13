"""Raster band tag management for geospatial raster datasets.

This module provides the BandTags class for managing and manipulating metadata
tags associated with individual bands in raster datasets. The implementation
integrates with rasterio for reading and writing band-specific metadata while
providing a structured interface for tag organization, validation, and manipulation.

BandTags instances are immutable by design, with all modification operations
returning new instances rather than modifying existing objects.

Band indices follow rasterio conventions starting from 1, aligning with
standard GIS and remote sensing practices for band numbering in multi-band
raster datasets.

Tag modification operations require write access to raster files and may
modify file metadata permanently. Always backup important raster datasets
before performing metadata write operations, especially in production
environments where data integrity is critical.

Classes:
    BandTags: A metadata container for managing key-value tags associated with
        individual raster bands. Provides methods for tag manipulation, raster
        integration, and metadata organization with validation and immutability
        support for reliable metadata handling.

Examples:
    Basic band tag management and manipulation:

    >>> # Create band tags for RGB imagery
    >>> rgb_tags = BandTags({
    ...     1: {'classification': 'red', 'wavelength': '650nm'},
    ...     2: {'classification': 'green', 'wavelength': '550nm'},
    ...     3: {'classification': 'blue', 'wavelength': '450nm'}
    ... })
    >>> print(f"Tagged bands: {rgb_tags.band_indices}")
    Tagged bands: {1, 2, 3}

    Raster integration and metadata persistence:

    >>> # Load existing tags from raster file
    >>> existing_tags = BandTags.from_raster("satellite_image.tif")
    >>>
    >>> # Add new classification tags
    >>> updated_tags = existing_tags.put_band_tags(1, {'landcover': 'vegetation'})
    >>>
    >>> # Write updated tags back to raster
    >>> updated_tags.write_tags("satellite_image.tif")
"""

from __future__ import annotations

from copy import deepcopy
from typing import Set

import rasterio

from rasterio.io import DatasetReader, DatasetWriter


class BandTags:
    """Manages metadata tags for individual bands in raster datasets.

    BandTags provides a structured approach to handling band-specific metadata
    in multi-band raster datasets, supporting tag organization, validation, and
    integration with rasterio datasets. The class maintains immutability for
    safe metadata operations while offering flexible tag manipulation and
    persistence capabilities.

    Attributes:
        tags (dict[int, dict[str, str]]): A nested dictionary mapping band indices
            to their associated metadata tags. Band indices are positive integers
            starting from 1, following rasterio conventions.

    Examples:
        Create band tags for multispectral imagery:

        >>> # Define tags for Landsat-style bands
        >>> landsat_tags = BandTags({
        ...     1: {'band_name': 'coastal', 'wavelength': '443nm'},
        ...     2: {'band_name': 'blue', 'wavelength': '482nm'},
        ...     3: {'band_name': 'green', 'wavelength': '562nm'},
        ...     4: {'band_name': 'red', 'wavelength': '655nm'}
        ... })
        >>> print(f"Number of bands: {landsat_tags.count}")
        Number of bands: 4
    """

    tags: dict[int, dict[str, str]]

    def __init__(self, tags: dict[int, dict[str, str]] | None = None):
        """Initialize BandTags with optional tag dictionary and validation.

        Args:
            tags (dict[int, dict[str, str]] | None, optional): A nested dictionary
                mapping band indices to their metadata tags. Band indices must be
                positive integers starting from 1. If None, creates an empty BandTags
                instance ready for tag addition through other methods.

        Raises:
            ValueError: Raised when band indices are invalid, including non-integer
                values, zero, or negative numbers. This validation ensures compliance
                with rasterio band numbering conventions and prevents indexing errors
                in subsequent raster operations.
        """
        if tags:
            _validate_band_indices(tags)
            self.tags = deepcopy(tags)
        else:
            self.tags = {}

    # properties ------------------------------------------------------------------
    @property
    def band_indices(self) -> Set[int]:
        """Get the set of band indices that have tags.

        Returns:
            Set[int]: A set of positive integers representing band indices that
                have associated metadata tags. Returns an empty set if no bands
                have been tagged. Band indices follow rasterio conventions
                starting from 1.

        Examples:
            Check which bands have metadata:

            >>> tags = BandTags({1: {'type': 'red'}, 3: {'type': 'blue'}})
            >>> print(f"Tagged bands: {sorted(tags.band_indices)}")
            Tagged bands: [1, 3]
        """
        return set(self.tags.keys())

    @property
    def tags_by_band(self) -> dict[str, dict[str, int]]:
        """Organize tags by tag names with values mapped to band indices.

        Creates a reverse mapping of the tag structure, organizing tags by their
        names rather than by band indices. This property enables searching for
        bands by tag values and analyzing tag distribution across bands.

        Returns:
            dict[str, dict[str, int]]: A nested dictionary where outer keys are
                tag names and inner dictionaries map tag values to the band indices
                that contain those values. This structure enables efficient lookup
                of bands by tag criteria and analysis of tag value distribution.

        Examples:
            Find bands by classification:

            >>> tags = BandTags({
            ...     1: {'type': 'visible', 'color': 'red'},
            ...     2: {'type': 'visible', 'color': 'green'},
            ...     3: {'type': 'infrared', 'range': 'near'}
            ... })
            >>> print(tags.tags_by_band)
            {'type': {'visible': 2, 'infrared': 3}, 'color': {'red': 1, 'green': 2}, 'range': {'near': 3}}
            >>> by_type = tags.tags_by_band['type']
            >>> print(f"Visible bands: {by_type['visible']}")
            Visible bands: 2
            >>> print(f"Infrared bands: {by_type['infrared']}")
            Infrared bands: 3

            Analyze tag value distribution:

            >>> color_distribution = tags.tags_by_band.get('color', {})
            >>> print(f"Color bands: {color_distribution}")
            Color bands: {'red': 1, 'green': 2}
        """
        tags_by_band = {}
        for band_idx, tags in self.tags.items():
            for tag_name, tag_value in tags.items():
                if tag_name not in tags_by_band:
                    tags_by_band[tag_name] = {}
                tags_by_band[tag_name][tag_value] = band_idx

        return tags_by_band

    @property
    def count(self) -> int:
        """Get the highest band index that has associated tags.

        This property is intended to match the behavior of rasterio.DatasetReader.count.

        Returns:
            int: The highest band index with associated tags, or 0 if no bands
                are tagged. This value may not equal the total number of tagged
                bands if band indices are not consecutive.

        Examples:
            Check maximum band index:

            >>> consecutive_tags = BandTags({1: {'a': 'b'}, 2: {'c': 'd'}, 3: {'e': 'f'}})
            >>> print(f"Max band index: {consecutive_tags.count}")
            Max band index: 3

            Non-consecutive band indices:

            >>> sparse_tags = BandTags({1: {'a': 'b'}, 5: {'c': 'd'}})
            >>> print(f"Max band index: {sparse_tags.count}")
            Max band index: 5
            >>> print(f"Tagged band count: {len(sparse_tags.band_indices)}")
            Tagged band count: 2
        """
        return max(self.tags.keys()) if self.tags else 0

    @property
    def tag_names(self) -> Set[str]:
        """Get all unique tag names used across all bands.

        Returns a set containing all tag names that appear in any band's metadata,
        providing an overview of the metadata schema.

        Returns:
            Set[str]: A set of unique tag names used across all tagged bands.
                Returns an empty set if no bands are tagged. Tag names represent
                the keys in band metadata dictionaries.

        Examples:
            Analyze metadata schema:

            >>> tags = BandTags({
            ...     1: {'type': 'visible', 'wavelength': '650nm', 'quality': 'high'},
            ...     2: {'type': 'visible', 'wavelength': '550nm'},
            ...     3: {'type': 'infrared', 'quality': 'medium'}
            ... })
            >>> schema = tags.tag_names
            >>> print(f"Available tag types: {sorted(schema)}")
            Available tag types: ['quality', 'type', 'wavelength']

            Check for consistent tagging:

            >>> required_tags = {'type', 'wavelength'}
            >>> missing_tags = required_tags - schema
            >>> print(f"Schema complete: {len(missing_tags) == 0}")
            Schema complete: True
        """
        tag_names = set()
        for tags in self.tags.values():
            tag_names.update(tags.keys())

        return tag_names

    # methods ---------------------------------------------------------------------
    def get_band_tags(self, band_index: int) -> dict[str, str]:
        """Retrieve tags for a specific band.

        Args:
            band_index (int): The band index for which to retrieve tags. Must be
                a positive integer following rasterio band numbering conventions.

        Returns:
            dict[str, str]: A dictionary containing all tag key-value pairs for
                the specified band. Returns an empty dictionary if the band has
                no associated tags. The returned dictionary is a copy and can be
                safely modified without affecting the BandTags instance.

        Examples:
            Retrieve tags for specific bands:

            >>> tags = BandTags({
            ...     1: {'color': 'red', 'type': 'visible'},
            ...     2: {'color': 'green', 'type': 'visible'}
            ... })
            >>> red_tags = tags.get_band_tags(1)
            >>> print(red_tags)
            {'color': 'red', 'type': 'visible'}
        """
        return self.tags[band_index].copy() if band_index in self.tags else {}

    def put_band_tags(self, band_index: int, tags: dict[str, str]) -> BandTags:
        """Create a new BandTags instance with additional or updated tags for a band.

        Args:
            band_index (int): The band index for which to add or update tags.
                Must be a positive integer following rasterio conventions. If
                the band already has tags, the new tags will be merged with
                existing ones, with new values overriding existing keys.
            tags (dict[str, str]): A dictionary of tag key-value pairs to add
                or update for the specified band. All keys and values must be
                strings to maintain consistency with rasterio metadata handling.

        Returns:
            BandTags: A new BandTags instance containing the updated tag structure.
                The original BandTags instance remains unchanged. If the band
                already had tags, they are merged with the new tags, with new
                values taking precedence for duplicate keys.

        Examples:
            Add tags to new band:

            >>> original = BandTags({1: {'color': 'red'}})
            >>> updated = original.put_band_tags(2, {'color': 'green', 'type': 'visible'})
            >>> print(f"Updated bands: {sorted(updated.band_indices)}")
            Updated bands: [1, 2]

            Update existing band tags:

            >>> enhanced = updated.put_band_tags(1, {'type': 'visible', 'quality': 'high'})
            >>> red_tags = enhanced.get_band_tags(1)
            >>> print(red_tags)
            {'color': 'red', 'type': 'visible', 'quality': 'high'}

            Chain tag additions:

            >>> final = (BandTags()
            ...          .put_band_tags(1, {'color': 'red'})
            ...          .put_band_tags(2, {'color': 'green'})
            ...          .put_band_tags(3, {'color': 'blue'}))
            >>> print(f"RGB bands: {sorted(final.band_indices)}")
            RGB bands: [1, 2, 3]
        """
        band_tags = (
            {**self.tags[band_index], **tags} if band_index in self.tags else tags
        )

        return BandTags({**self.tags, band_index: band_tags})

    def write_tags(self, raster: str | DatasetWriter) -> None:
        """Write band tags to a raster dataset file or writer object.

        Persists all band metadata tags to the specified raster dataset, either
        by opening a file path for writing or using an existing DatasetWriter
        instance.

        Args:
            raster (str | DatasetWriter): The target raster for tag writing.
                Can be either a file path string for automatic file opening
                or an existing DatasetWriter instance for direct writing.
                File paths must reference writable raster files, while
                DatasetWriter instances must be open and have write permissions
                (opened with either "w" or "r+").

        Examples:
            Write tags to raster file:

            >>> tags = BandTags({
            ...     1: {'classification': 'water', 'confidence': 'high'},
            ...     2: {'classification': 'vegetation', 'confidence': 'medium'}
            ... })
            >>> tags.write_tags("classified_image.tif")

            Write tags using existing writer:

            >>> import rasterio
            >>> with rasterio.open("output.tif", "w", **profile) as dst:
            ...     tags.write_tags(dst)
        """
        if isinstance(raster, DatasetWriter):
            return self._write_tags(raster)

        with rasterio.open(raster, "r+") as src:
            return self._write_tags(src)

    def _write_tags(self, raster: DatasetWriter) -> None:
        """Internal method to write tags to an open DatasetWriter."""
        for band, tags in self.tags.items():
            raster.update_tags(band, **tags)

    # static methods --------------------------------------------------------------
    @staticmethod
    def from_raster(raster: str | DatasetReader) -> BandTags:
        """Create a BandTags instance from an existing raster dataset.

        Reads all band tags from the specified raster dataset and
        constructs a new BandTags instance containing the extracted tags.

        The method extracts tags exactly as stored in the raster file
        without modification. Empty tag dictionaries for bands without
        tags are not included in the resulting BandTags object.

        Args:
            raster (str | DatasetReader): The source raster dataset for tag
                extraction. Can be either a file path string for automatic
                file opening or an existing DatasetReader instance for direct
                reading. File paths must reference readable raster files with
                valid tags.

        Returns:
            BandTags: A new BandTags instance containing all band tags extracted
                from the source raster.

        Examples:
            Load tags from raster file:

            >>> existing_tags = BandTags.from_raster("satellite_image.tif")
            >>> print(f"Loaded tags for {len(existing_tags.band_indices)} bands")

            Load tags from open dataset:

            >>> import rasterio
            >>> with rasterio.open("multispectral.tif") as src:
            ...     tags = BandTags.from_raster(src)
            ...     schema = tags.tag_names
            ...     print(f"Available metadata: {sorted(schema)}")
        """
        if isinstance(raster, DatasetReader):
            return BandTags._from_datasetreader(raster)

        with rasterio.open(raster) as src:
            return BandTags._from_datasetreader(src)

    @staticmethod
    def _from_datasetreader(src: DatasetReader) -> BandTags:
        """Internal method to extract tags from an open DatasetReader."""
        band_tags = {}
        for band in range(1, src.count + 1):
            band_tags[band] = src.tags(band)

        return BandTags(band_tags)


# private helpers -----------------------------------------------------------------
def _validate_band_indices(tags: dict[int, dict[str, str]]) -> None:
    """Validate that all band indices are positive integers."""
    for band_idx in tags.keys():
        if not isinstance(band_idx, int) or band_idx < 1:
            raise ValueError(f"Band index must be a positive integer, got {band_idx}")

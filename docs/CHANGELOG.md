---
title: Changelog
date: 2024-10-08
authors:
  - name: A. Sina Booeshaghi
---

# Changelog

## [0.3.0] - XXXX-XX-XX (Unreleased)

### Added

- Added typing hints to many `Assay` and `Region` functions
- Added `'k key` to `seqspec info` to display one of `meta` for metadata, `sequence_spec` for sequence spec, and `library_spec` for library spec
- Added `-f format` to `seqspec info` to enable multiple formats for displaying info
- Added support for 0 length regions in the specification
- Added ability to modify reads using `seqspec modify`
- `seqspec init` now accepts read information
- Added templates and updated documentation to myst, website
- Added new examples (e.g., dogmaseq-dig)
- Added File object to Read
- Added SeqKit, SeqProtocol, LibKit, and LibProtocol attributes
- Added option to specify multiple SeqKit, SeqProtocol, LibKit, LibProtocol for each modality
- Added name validation against known list of SeqKit, SeqProtocol, LibKit, LibProtocol
- Added new attributes to Onlist object (Onlist now contains a File object):
  - filetype
  - filesize
  - url
- Added "file_id" to the File object
- Added `seqspec file` command to return the list of files in the spec as paired across reads or interleaved
- Added `seqspec upgrade` hidden feature to upgrade v0.2.x seqspec files to v0.3.0.

### Changed

- Updated `seqspec index` to read strands for chromap
- Updated `seqspec split` to correctly split sequence_spec
- Modified `seqspec` string to use min_len instead of max_len to accommodate nanopore reads
- Updated documentation on how to propose new vocabulary
- Modified the internals of `seqspec onlist` to manage saving the joined onlist to the `-o` location when specified (otherwise saves to path where spec lives).
- Renamed "location" to "urltype" in Onlist object
- Replaced `-r` with `-i` id type for all functions (deprecated `-r`)
- Multiple seqspec commands now require the addition of a `-s selector [read, region, file]`
- `seqspec index` can now take in reads, regions, or files and index
- `seqspec modify` can now add files to the template
- Updated splitseq template

### Fixed

- Fixed `seqspec onlist` functionality
- Fixed error enumeration in seqspec check

### Removed

TODO:

- Remove `lib_struct`
- Remove `parent_id`

### Breaking Changes

- File elements are now required in Read objects and Onlist objects in version 0.3.0

## [0.2.0] - 2024-04-17

### Changed

- `seqspec index` uses primer and max length of of supplied Read
- `assay_spec` renamed `library_spec`
- Reorganize specification document
- Move contribution guidelines from `SPECIFICATION.md` to `CONTRIBUTION.md`
- Move example `Region`s from `SPECIFCATION.md` to `seqspec/docs/regions`
- `seqspec index` defaults to indexing reads, `--region` indexes regions
- Change descriptors of attributes `assay_id`, `doi`
- `Assay` attribute `assay` changed to `assay_id`
- `Read` attribute `read_name` changed to `name`
- `Assay` attribute `publication_date` changed to `date`
- `Assay` attribute `sequencer` changed to `sequence_protocol`
- `Assay` function `get_modality` changed to `get_libspec`
- `Region` function `update_attr` uses the `max_len` to generate `random` and `onlist` sequence lengths instead of `min_len`
- `get_region_by_type` changed to `get_region_by_region_type` to disambiguate between `region_type` and `sequence_type`
- `seqspec onlist` (by default) searches for onlists in the `Region`s intersected by the `Read` passed to `-r`.
- Support older versions of matplotlib by handling the `spines[["top", "bottom"...]]` structure
- Increase the number of Xs in the random region to match `max_len` for validation
- Update `seqspec print` command to use the replacement `assay_id` attribute instead of `assay`
- Implement downloading onlists via URLs and transparently decompress gzip files
- Change `read_list` function to take the `onlist` object for handling local and remote files
- Added `onlist` argument to specify combined barcode list file format (kallisto's multi-file format and default cartesian product format)

### Added

- Added `sequence_spec` in the `Assay` object
- Added `Read` object in the `sequence_spec` object
- Added `sequence_spec` to the seqspec json schema
- Added `Read` object to specification document
- Added `Read` generator to website GUI
- Added pattern matching to `date` in `Assay` (expected date format: DAY MONTH YEAR, where day is one or two numbers, month is the full named month starting with a Capital letter and year is the full year)
- Added `library_kit` to `Assay` object (kit that adds seq adapters)
- Added `library_protocol` to `Assay` object (library that generates insert)
- Added `sequence_kit` to `Assay` object
- Added website to view example `seqspec` objects
- Added `get_seqspec` to assay returns sequence structure for a given modality
- Added multiple checks to `seqspec check`
  - check read modalities exist in assay modalities
  - check primer ids from seqspec are unique and exists as region ids in libspec
  - check that the primer id exists as an atomic region (currently a strong assumption that may be relaxed in the future)
  - check properties of multiple sequence types
    - `fixed` and `regions` not null incompatible
    - `joined` and `regions` null incompatible
    - `random` and `regions` not null incompatible
    - `random` must have `sequence` of all X's
    - `onlist` and `onlist` property null incompatible
  - check that the min len is less than or equal to the max len
  - check that the length of the sequence is between min and max len
  - Note a strong assumption in `seqspec print` is that the sequence have a length equal to the `max_len` for visualization purposes
- Added `RegionCoordinate` object that maps `Region` min/max lengths to 0-indexed positions
- `seqspec onlist` searches for onlists in a `Region` based on `--region` flag
- Added type annotations for `join_onlists` to clarify it needs a list of `Onlist` objects
- Added minimal tests for `RegionCoordinate`, `project_regions_to_coordinates`, `run_onlist_region`, `run_onlist_read`, and seqspec print functions
- Added list of options to CLI for `-f FORMAT` within `seqspec onlist` and `seqspec print`
- Added `-s SEQTYPE` to `seqspec print` to disambiguate printing `sequence`, `library`, or `libseq` objects. TODO wrap `seqspec info` into `seqspec print -f info`.
- Added `-s SPECOBJECT` to `seqspec onlist`. Specify specific object `read`, `region`, or `region-type` for finding the `onlist`.
- Added fetching ability for seqspec onlist from remote with IGVF credentials (credit to @detrout)

### Removed

TODO:

- Remove `lib_struct`
- Remove `parent_id`

### Fixed

- Sequencing overlapping pairs now supported
- `seqspec check` correctly handles sequences lengths longer than the stated min/max range
- Fixed test for `project_regions_to_coordinates`
- Get the test of seqspec check working again by updating the schema for the refactored example specification YAML files and mocking fastq and barcode files
- Only return the onlist filename if it's a local file, downloading remote lists when needed

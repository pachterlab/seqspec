# Changelog

## [0.2.0] - 2024-02-XX

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
- Add `onlist` argument to specify combined barcode list file format (kallisto's multi-file format and default cartesian product format)

### Added

- Add `sequence_spec` in the `Assay` object
- Add `Read` object in the `sequence_spec` object
- Add `sequence_spec` to the seqspec json schema
- Add `Read` object to specification document
- Add `Read` generator to website GUI
- Add pattern matching to `date` in `Assay` (expected date format: DAY MONTH YEAR, where day is one or two numbers, month is the full named month starting with a Capital letter and year is the full year)
- Add `library_kit` to `Assay` object (kit that adds seq adapters)
- Add `library_protocol` to `Assay` object (library that generates insert)
- Add `sequence_kit` to `Assay` object
- Add website to view example `seqspec` objects
- Add `get_seqspec` to assay returns sequence structure for a given modality
- Add multiple checks to `seqspec check`
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
- Add `RegionCoordinate` object that maps `Region` min/max lengths to 0-indexed positions
- `seqspec onlist` searches for onlists in a `Region` based on `--region` flag
- Add type annotations for `join_onlists` to clarify it needs a list of `Onlist` objects
- Add minimal tests for `RegionCoordinate`, `project_regions_to_coordinates`, `run_onlist_region`, `run_onlist_read`, and seqspec print functions
- Add list of options to CLI for `-f FORMAT` within `seqspec onlist` and `seqspec print`
- Add `-s SEQTYPE` to `seqspec print` to disambiguate printing `sequence`, `library`, or `libseq` objects. TODO wrap `seqspec info` into `seqspec print -f info`.
- Add `-s SPECOBJECT` to `seqspec onlist`. Specify specific object `read`, `region`, or `region-type` for finding the `onlist`.
- Add fetching ability for seqspec onlist from remote with IGVF credentials (credit to @detrout)

### Removed

TODO:

- Remove `lib_struct`
- Remove `parent_id`

### Fixed

- Sequencing overlapping pairs now supported
- `seqspec check` correctly handles sequences lengths longer than the stated min/max range
- Fix test for `project_regions_to_coordinates`
- Get the test of seqspec check working again by updating the schema for the refactored example specification YAML files and mocking fastq and barcode files
- Only return the onlist filename if it's a local file, downloading remote lists when needed

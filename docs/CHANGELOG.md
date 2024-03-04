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

### Added

- Add `sequence_spec` in the `Assay` object
- Add `Read` object in the `sequence_spec` object
- Add `sequence_spec` to the seqspec json schema
- Add `Read` object to specification document
- Add `Read` generator to website GUI
- Add prior version seqspec schema to seqspec/schema (note to self, this must be done for every release)
- Add pattern matching to `date` in `Assay` (expected date format: DAY MONTH YEAR, where day is one or two numbers, month is the full named month starting with a Capital letter and year is the full year)
- Add `library_kit` to `Assay` object (kit that adds seq adapters)
- Add `library_protocol` to `Assay` object (library that generates insert)
- Add `sequence_kit` to `Assay` object
- Add website to view example `seqspec` objects
- Add `get_seqspec` to assay returns sequence structure for a given modality

### Removed

TODO:

- Remove `lib_struct`
- Remove `parent_id`

### Fixed

- Sequencing overlapping pairs now supported
- `seqspec check` correctly handles sequences lengths longer than the stated min/max range

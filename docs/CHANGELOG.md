# Changelog

## [0.2.0] - 2024-02-XX

### Changed

- `seqspec index` uses primer and max length of of supplied Read
- `assay_spec` renamed `library_spec`
- Reorganize specification document
- Move contribution guidelines from `SPECIFICATION.md` to `CONTRIBUTION.md`
- Move example `Region`s from `SPECIFCATION.md` to `seqspec/docs/regions`
- `seqspec index` defaults to indexing reads, `--region` indexes regions

### Added

- Add `sequence_spec` in the `Assay` object
- Add `Read` object in the `sequence_spec` object
- Add `sequence_spec` to the seqspec json schema
- Add `Read` object to specification document
- Add `Read` generator to website GUI

### Removed

-

### Fixed

- Sequencing overlapping pairs now supported

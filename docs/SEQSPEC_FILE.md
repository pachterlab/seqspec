---
title: File Format
date: 2024-07-12
authors:
  - name: A. Sina Booeshaghi
---

# Overview

seqspec is a machine-readable specification for annotating sequencing libraries produced by genomics assays. It provides a standardized format for describing the structure of sequencing libraries and the resulting sequencing reads.

The primary goal of a seqspec file is to:

1. Facilitate standardization of preprocessing steps across different assays
2. Enable data management and tracking
3. Simplify the interpretation and reuse of sequencing data

# Structure

A seqspec file consists of three main components:

1. **Assay Information**: Metadata about the assay, including identifiers, protocols, and kits used.
2. **Library Structure**: Description of the molecular components in the sequencing library.
3. **Read Structure**: Description of the sequencing reads generated from the sequencing library.

seqspec files are written in YAML format and can be created and edited in a text editor like VSCode, TextEdit, Notepad, or Sublime. The basic structure includes:

```yaml
seqspec_version: <version>
assay_id:
# + Assay metadata
modalities:
  # List of modalities (e.g., RNA, DNA, ATAC)
library_spec:
  # List of regions in the library
sequence_spec:
  # List of reads generated from the library
```

`modalities` contains a list of strings describing the types of molecules assayed. They come from a [controlled vocabulary](SPECIFICATION.md). Additional assay metadata includes library preparation kit and protocol as well as sequencing kit and protocol.

`seqspec` files can be manipulated and used with the `seqspec` command line tool.

## Library structure

The `library_spec` describes the "regions", or set of standard "blocks" such as a barcode, contained in the sequencing library. Each region is annotated with the following metadata:

- `region_id`: Unique identifier for the region
- `region_type`: Type of region (e.g., barcode, UMI, cDNA)
- `sequence_type`: Nature of the sequence (fixed, random, onlist)
- `sequence`: Actual or representative sequence
- `min_len` and `max_len`: Minimum and maximum length of the region

Each region can contain nested regions under the `regions` property. This means a valid library structure could look like:

```
region_1
|-region_2
  |--region_3
|-region_4
region_5
|-region_6
```

```{important}
The first "level" of the `library_spec` must have `region_ids` that correspond to the list of `modalities`. In the example above, the first level corresponds to the region ids `region_1` and `region_5`.
```

## Sequence structure

The `sequence_spec` contains a list of the sequencing "reads" generated from the `library_spec`. Each read is annotated with the following metadata:

- `read_id`: Identifier for the read
- `modality`: Associated modality
- `primer_id`: ID of the primer region in the library structure
- `strand`: Orientation of the read (pos or neg)
- `min_len` and `max_len`: Minimum and maximum length of the read

# Mapping Reads to Library Elements

The relationship between the `sequence_spec` and `library_spec` in `seqspec` is defined as follows:

1. Each read in the `sequence_spec` has a `primer_id` that corresponds to a unique `region_id` in the `library_spec`.
2. This `primer_id` indicates the starting point of the read within the library molecule.
3. The `min_len` and `max_len` properties of the read define how many bases are sequenced from this starting point.
4. The read encompasses all library elements that fall within its length, starting from the end of the `primer_id` region.
5. If the read is on the positive strand, it extends to the right of the primer; if on the negative strand, it extends to the left.

This mapping allows the precise identification the library elements captured in each sequencing read using the `seqspec index` command.

# Format requirements

The following requirements are often sources of errors when writing a `seqspec` file.

- Each `region_id` in top-most level of the `library_spec` should correspond to one modality in the `modalities`.
- The `primer_id` of each read in the `sequence_spec` must exist as a `region_id` in the `library_spec`

# Conclusion

`seqspec` provides a standardized way to describe complex genomics assays, facilitating data interpretation, preprocessing, and reanalysis. By clearly defining library structures and read configurations, it enables more efficient and accurate processing of sequencing data across different assays and platforms. For more information about the contents of a seqspec file, please see the [technical specification](SPECIFICATION.md).
---
title: Technical Specification
date: 2024-06-25
authors:
  - name: A. Sina Booeshaghi
---

# Introduction

`seqspec` is an open-source file format specification and command-line tool for annotating sequencing libraries that utilized YAML for data representation. This document outlines the specification and explains various use-cases.

# Schema Overview

The `seqspec` schema is designed to annotate sequencing libraries through three main objects: `Assay`, `Region`, and `Read` objects. `Assay` objects contain `Region` objects, possibly nested, which can be orthogonally annotated with `Read` objects. The `Assay` object is the parent object and describes the structure of the molecules in a sequencing library (the library specification) as well as the structure of the reads obtained after sequencing the sequencing library (the sequence specification).

Each seqspec file is associated with a sequencing run and documents the designed library structure and the designed read structure. A simple (but incomplete example) looks like the following:

```yaml
modalities:
  - Modality1
  - Modality2
sequence_spec:
  - read_id: Read1
    modality: Modality1
    primer_id: Region2
    strand: pos
    ...
library_spec:
  - region_id: Modality1
    regions:
      - region_id: Region1
        ...
      - region_id: Region2
        ...
  - region_id: Modality2
```

In order to catalogue relevant information for each library structure, multiple properties are specified for each `Assay` and each `Region`. A description of the `Assay` and `Region` schema can be found in `seqspec/schema/seqspec.schema.json`.

## `Assay` Object

The `Assay` object contains overall metadata for the sequencing run.

Fields:

- `seqspec_version`: String specifying the version of the seqspec specification, adhering to [semantic versioning](https://semver.org/).
- `assay_id`: Identifier for the assay.
- `name`: The name of the assay.
- `doi`: The doi of the paper that describes the assay.
- `date`: The seqspec creation date, in "DD Month YYYY" format.
- `description`: A short description of the assay.
- `modalities`: The modalities the assay targets. Can be one or more of "dna", "rna", "tag", "protein", "atac", "crispr".
- `lib_struct`: The link to Teichmann's libstructs page derived for this sequence.
- `library_protocol`: The protocol/machine/tool to generate the library insert.
- `library_kit`: The kit used to make the library sequence_protocol compatible.
- `sequence_protocol`: The protocol/machine/tool to generate sequences.
- `sequence_kit`: The kit used with the protocol to sequence the library.
- `sequence_spec`: The spec for the sequencer, an array of Read objects.
- `library_spec`: The spec for the assay, an array of Region objects.

Example:

```yaml
!Assay
seqspec_version: 0.0.0
assay_id: SPLiT-seq/Illumina
name: SPLiT-seq
doi: https://doi.org/10.1126/science.aam8999
date: 15 March 2018
description: split-pool ligation-based transcriptome sequencing
modalities:
  - rna
lib_struct: https://teichlab.github.io/scg_lib_structs/methods_html/SPLiT-seq.html
library_protocol: SPLiT-seq
library_kit: Custom
sequence_protocol: Illumina NextSeq 500
sequence_kit: Illumina NextSeq 500 High Output Kit v2.5 (150 Cycles)
sequence_spec: ...
library_spec: ...
```

## `Region` Object

The `library_structure` contains a list of, possibly nested, `Region objects` which detail individual segments within the sequencing library molecule, specifying types, sequences, and relationships between segments.

- `region_id` is a free-form string and must be unique across all regions in the `seqspec` file.
  - if the assay contains multiple regions of the same `region_type` it may be useful to append an integer to the end of the `region_id` to differentiate those regions. For example, if the assay had four `barcodes` then each of the individual `barcode` regions could have the `region_id`s `barcode-1`, `barcode-2`, `barcode-3`, `barcode-4`.
- `region_type` can be one of the following:
  - `atac`: The modality for chromatin accesibility capture
  - `barcode`: A region corresponding to a synthetic barcode sequence often associated with samples or cells
  - `cdna`: Complementary DNA generated from an RNA product
  - `crispr`: The modality for barcode-based CRISPR assay
  - `custom_primer`: A synthesized segment of nucleic acid used to initiate DNA synthesis.
  - `dna`: Deoxyribonucleic acid, targets often generated for MPRA assays.
  - `fastq`: A region corresponding to a FASTQ file.
  - `fastq_link`: A region corresponding to a FASTQ file that is stored remotely (via url).
  - `gdna`: Genomic DNA, targets often obtained with ATACseq.
  - `hic`: The modality corresponding to high-throughput chromosome conformation capture, a technique for studying the three-dimensional structure of genomes.
  - `illumina_p5`: A sequencing primer specific to Illumina platforms, used to bind the library molecule to the flow cell.
  - `illumina_p7`: A sequencing primer specific to Illumina platforms, used to bind the library molecule to the flow cell.
  - `index5`: A barcode sequence used for multiplexing and sample identification in sequencing, associated with the P5 end.
  - `index7`: A barcode sequence used for multiplexing and sample identification in sequencing, associated with the P7 end.
  - `linker`: A short, synthetic DNA sequence used to connect two molecules or fragments.
  - `ME1`: Mosaic end 1, used in the Nextera Library kit for library preparation.
  - `ME2`: Mosaic end 2, used in the Nextera Library kit for library preparation.
  - `methyl`: The modality for methylation sequencing which assays the presence of a methyl group.
  - `named`: A custom named region for grouping other regions.
  - `nextera_read1`: A read sequence obtained from the first end in paired-end Nextera library sequencing.
  - `nextera_read2`: A read sequence obtained from the second end in paired-end Nextera library sequencing.
  - `poly_A`: A sequence of multiple adenine nucleotides.
  - `poly_G`: A sequence of multiple guanine nucleotides.
  - `poly_T`: A sequence of multiple thymine nucleotides.
  - `poly_C`: A sequence of multiple cytosine nucleotides.
  - `protein`: The modality corresponding to assaying cell-surface proteins.
  - `rna`: The modality corresponding to assaying RNA.
  - `s5`: A sequencing primer or adaptor typically used in the Nextera kit in conjunction with ME1.
  - `s7`: A sequencing primer or adaptor typically used in the Nextera kit in conjunction with ME2.
  - `tag`: A short sequence of DNA or RNA used to label or identify a sample, protein, or other grouping.
  - `truseq_read1`: The first read primer in a paired-end sequencing run using the Illumina TruSeq Library preparation kit.
  - `truseq_read2`: The second read primer in a paired-end sequencing run using the Illumina TruSeq Library preparation kit.
  - `umi`: Unique Molecular Identifier, a short nucleotide sequence used to tag individual molecules.
- `sequence_type` can be one of the following:
  - `fixed` indicates that sequence string is known
  - `joined` indicates that the sequence is created (joined) from nested regions
  - `onlist` indicates that the sequence is derived from an onlist (if specified, then `onlist` must be non-null
  - `random` indicates that the sequence is not known a-priori
- `sequence` is a representation of the sequence, must match the pattern `^[ACGTRYMKSWHBVDNX]+$`
  - if the `sequence_type` is `fixed` then the actual sequence string is provided
  - if the `sequence_type` is `joined` then field must be the concatenation of the nested regions
  - if the `sequence_type` is `onlist` then field must an `N` string of length of the shortest sequence on the onlist
  - if the `sequence_type` is `random` then the field must be an `X` string
- `min_len` is an integer greater than or equal to 0 and less than or equal to 2048. It represents the minimum possible length of the `sequence`
- `max_len` is an integer greater than or equal to 0 and less than or equal to 2048. It represents the maximum length of the `sequence`
- `onlist` can be `null` or contain
  - `location` denotes whether the filename is a local path to a file or a URI to a file.
  - `filename` which is a path relative to the `seqspec` file containing a list of sequences
  - `md5` is the md5sum of the uncompressed file in `filename`, must match the pattern `^[a-f0-9]{32}$`
- `regions` can either be `null` or contain a list of `regions` as specified above.

Example:

```yaml
!Region
region_id: barcode-1
region_type: barcode
sequence_type: onlist
sequence: NNNNNNNN
min_len: 8
max_len: 8
onlist: !Onlist
  location: local
  filename: barcode-1_onlist.txt
  md5: 5b62453df2771f5aa856f78797f16591
regions: null
```

For more information about the specification of the various fields, please see the JSON schema representation of the various fields described above (`seqspec/schema/seqspec.schema.json`). For consistency across assays I suggest the following standard naming conventions for common regions. Please see `seqspec/docs/regions` for a list of example regions.

## Read Object

The `sequence_structure` contains a list of `Read` objects which describe the sequencing "reads" that are generated from sequencing the molecule described in the `library_structure`. A crucial concept is that `Read` objects contain a `primer_id` which maps to a single `region_id` in the `library_structure`.

Fields:

- `read_id`: The unique identifier for the read.
- `name`: The name of the read.
- `modality`: The modality of the assay generating the read.
- `primer_id`: The region id of the primer used.
- `min_len`: The minimum length of the read, must be greater than or equal to 0.
- `max_len`: The maximum length of the read, must be greater than 0.
- `strand`: The strand orientation of the read, either positive ('pos') or negative ('neg').

Example:

```yaml
- !Read
  read_id: read_001
  name: Read 1 of Sample A
  modality: rna
  primer_id: primer_25
  min_len: 50
  max_len: 300
  strand: pos
```

## YAML Tags

seqspec files contains YAML tags (strings prepended with an exclamation point `!`) to describe the various objects (`Assay`, `Region`, `Onlist`, `Read`). These tags make it easy to load `seqspec` files into python as a python object. Python manipulation of seqspec files becomes straightforward with "dot notation":

```python
from seqspec.utils import load_spec

spec = load_spec("seqspec/assays/10x-RNA-v3/spec.yaml")

print(spec.get_libspec("RNA").sequence)
# AATGATACGGCGACCACCGAGATCTACACTCTTTCCCTACACGACGCTCTTCCGATCTNNNNNNNNNNNNNNNNNNNNNNNNNNNNXAGATCGGAAGAGCACACGTCTGAACTCCAGTCACNNNNNNNNATCTCGTATGCCGTCTTCTGCTTG
```

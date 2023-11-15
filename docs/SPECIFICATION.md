# Specification

`seqspec` stands for "Sequence Specification" and is a file format for annotating sequencing reads. The file is written in YAML and can be manipulated with the `seqspec` command line tool.

## Terminology and Concepts

Each `spec` is described by two objects: the `Assay` object and the `Region` object. A library is described by one `Assay` object and multiple (possibly nested) `Region` objects. The `Region` objects are grouped with a `join` operation and an `order` on the sub`Region`s specified. A simple (but not fully specified example) looks like the following:

```
modalities:
    - Modality1
    - Modality2
assay_spec:
    - region_id: Modality1
      regions:
          - region_id: Region1
              ...
          - region_id: Region2
              ...
    - region_id: Modality2
        ...
```

In order to catalogue relevant information for each library structure, multiple properties are specified for each `Assay` and each `Region`. A description of the `Assay` and `Region` schema can be found in `seqspec/schema/seqspec.schema.json`.

### `Assay` parameters

Below is an example of an `Assay`.

```yaml
!Assay
seqspec_version: 0.0.0
assay: SPLiT-seq
sequencer: Illumina NextSeq500
name: SPLiT-seq/Illumina
doi: https://doi.org/10.1126/science.aam8999
publication_date: 15 March 2018
description: split-pool ligation-based transcriptome sequencing
modalities:
  - RNA
lib_struct: https://teichlab.github.io/scg_lib_structs/methods_html/SPLiT-seq.html
assay_spec:
	...
```

The following terms fully specify an `Assay`

- `seqspec_version`: a [semver](https://semver.org/) string that specifies the specification version
- `assay`: is a free-form string that labels the assay
- `sequencer`: is a free-form string that labels sequencer
- `name` is a string that identifies the assay/sequencer combination that produces reads
- `doi` is the doi link to the paper/protocol that describes the assay (if it exists)
- `publication_date` is the date the assay was published (linked to by the `doi`). Must be in DD Month Year format.
- `description` is a free-form string that describes the assay
- `modalities` is a list of `region_types` that are contained within the library. Each string must be present in exactly one `Region` in the first "level" of the `assay_spec`.
- `lib_struct` is a link to the manually annotated library structure developed by Xi Chen in Sarah Teichmann's lab.
- `assay_spec` is a list of `Regions`.

### `Region` parameters

Below is an example of a `Region`.

```yaml
!Region
region_id: barcode-1
region_type: barcode
name: barcode-1
sequence_type: onlist
sequence: NNNNNNNN
min_len: 8
max_len: 8
onlist: !Onlist
  filename: barcode-1_onlist.txt
  location: local
  md5: null
regions: null
```

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
- `name` is a free-form string for describing the region
- `sequence_type` can be one of the following:
  - `fixed` indicates that sequence string is known
  - `joined` indicates that the sequence is created (joined) from nested regions
  - `onlist` indicates that the sequence is derived from an onlist (if specified, then `onlist` must be non-null
  - `random` indicates that the sequence is not known a-priori
- `sequence` is a representation of the sequence
  - if the `sequence_type` is `fixed` then the actual sequence string is provided
  - if the `sequence_type` is `joined` then field must be the concatenation of the nested regions
  - if the `sequence_type` is `onlist` then field must an `N` string of length of the shortest sequence on the onlist
  - if the `sequence_type` is `random` then the field must be an `X` string
- `min_len` is an integer greater than or equal to zero. It represents the minimum possible length of the `sequence`
- `max_len` is an integer greater than or equal to the `min_len`. It represents the maximum length of the `sequence`
- `onlist` can be `null` or contain
  - `filename` which is a path (relative to the `seqspec` file containing a list of sequences
  - `location` denotes whether the filename is a local path to a file or a URI to a file.
  - `md5` is the md5sum of the uncompressed file in `filename`
- `regions` can either be `null` or contain a list of `regions` as specified above.

For more information about the specification of the various fields, please see `seqspec.schema.json` which is the JSON schema representation of the various fields described above.

### YAML Tags

The YAML file contains tags (strings prepended with an exclamation point `!`) to describe the various objects (`Assay`, `Region`, `Onlist`). The purpose of these tags is to make it easy to load the `seqspec` into python as a python object. This makes it possibe to access the various attrbiutes of the `seqspec` file with "dot notation" as follows:

```python
from seqspec.utils import load_spec

spec = load_spec("seqspec/assays/10x-RNA-v3/spec.yaml")

print(specA.get_modality("RNA").sequence)
# AATGATACGGCGACCACCGAGATCTACACTCTTTCCCTACACGACGCTCTTCCGATCTNNNNNNNNNNNNNNNNNNNNNNNNNNNNXAGATCGGAAGAGCACACGTCTGAACTCCAGTCACNNNNNNNNATCTCGTATGCCGTCTTCTGCTTG
```

## Named `Regions`

For consistency across assays I suggest the following naming conventions for standard regions. Note that the `region_id` for all atomic regions should be unique.

```yaml
# Assay region
!Assay
seqspec_version: 0.0.0
assay: My-RNA-Assay
sequencer: MySequencr
name: My-RNA-Assay/MySeq
doi: mydoi.org
publication_date: 01 January 2001
description: My custom assay
modalities:
  - RNA
lib_struct: www.link-to-libstructs.com
assay_spec:
  - !Region
    region_id: RNA
    region_type: RNA
    name: My RNA
    sequence_type: joined
    sequence:
    min_len: 0
    max_len: 0
    onlist:
    regions:
```

```yaml
# illumina_p5
- !Region
  region_id: illumina_p5
  region_type: illumina_p5
  name: illumina_p5
  sequence_type: fixed
  sequence: AATGATACGGCGACCACCGAGATCTACAC
  min_len: 29
  max_len: 29
  onlist:
  regions:

# illumina_p7
- !Region
  region_id: illumina_p7
  region_type: illumina_p7
  name: illumina_p7
  sequence_type: fixed
  sequence: ATCTCGTATGCCGTCTTCTGCTTG
  min_len: 24
  max_len: 24
  onlist:
  regions:

# nextera_read1
- !Region
  region_id: nextera_read1
  region_type: nextera_read1
  name: nextera_read1
  sequence_type: fixed
  sequence: fixed
  min_len: 33
  max_len: 33
  onlist:
  regions:
    - !Region
      region_id: s5
      region_type: s5
      name: s5
      sequence_type: TCGTCGGCAGCGTC
      sequence: fixed
      min_len: 14
      max_len: 14
      onlist:
      regions:
    - !Region
      region_id: ME1
      region_type: ME1
      name: ME1
      sequence_type: AGATGTGTATAAGAGACAG
      sequence: fixed
      min_len: 19
      max_len: 19
      onlist:
      regions:

# nextera_read2
- !Region
  region_id: nextera_read2
  region_type: nextera_read2
  name: nextera_read2
  sequence_type: joined
  sequence: CTGTCTCTTATACACATCTCCGAGCCCACGAGAC
  min_len: 34
  max_len: 34
  onlist:
  regions:
    - !Region
      region_id: ME2
      region_type: ME2
      name: ME2
      sequence_type: fixed
      sequence: CTGTCTCTTATACACATCT
      min_len: 19
      max_len: 19
      onlist:
      regions:
    - !Region
      region_id: s7
      region_type: s7
      name: s7
      sequence_type: fixed
      sequence: CCGAGCCCACGAGAC
      min_len: 15
      max_len: 15
      onlist:
      regions:

# truseq_read1
- !Region
  region_id: truseq_read1
  region_type: truseq_read1
  name: truseq_read1
  sequence_type: fixed
  sequence: ACACTCTTTCCCTACACGACGCTCTTCCGATCT
  min_len: 33
  max_len: 33
  onlist:
  regions:

# truseq_read2
- !Region
  region_id: truseq_read2
  region_type: truseq_read2
  name: truseq_read2
  sequence_type: fixed
  sequence: AGATCGGAAGAGCACACGTCTGAACTCCAGTCAC
  min_len: 34
  max_len: 34
  onlist:
  regions:

# index5
- !Region
  region_id: I2.fastq.gz
  region_type: I2.fastq.gz
  name: Index 2 FASTQ
  sequence_type: joined
  sequence: NNNNNNNN
  min_len: 8
  max_len: 8
  onlist:
  regions:
    - !Region
      region_id: index5
      region_type: index5
      name: index5
      sequence_type: onlist
      sequence: NNNNNNNN
      min_len: 8
      max_len: 8
      onlist: !Onlist
        filename: index5_onlist.txt
        location: local
        md5: null
      regions:

# index7
- !Region
  region_id: I1.fastq.gz
  region_type: I1.fastq.gz
  name: Index 1 FASTQ
  sequence_type: joined
  sequence: NNNNNNNN
  min_len: 8
  max_len: 8
  onlist:
  regions:
    - !Region
      region_id: index7
      region_type: index7
      name: index7
      sequence_type: onlist
      sequence: NNNNNNNN
      min_len: 8
      max_len: 8
      onlist: !Onlist
        filename: index7_onlist.txt
        location: local
        md5: null
      regions:

# Read 1 Fastq
- !Region
  region_id: R1.fastq.gz
  region_type: R1.fastq.gz
  name: Read 1 FASTQ
  sequence_type: joined
  sequence:
  min_len: 0
  max_len: 0
  onlist:
  regions:

# Read 2 Fastq
- !Region
  region_id: R2.fastq.gz
  region_type: R2.fastq.gz
  name: Read 2 FASTQ
  sequence_type: joined
  sequence:
  min_len: 0
  max_len: 0
  onlist:
  regions:

# barcode
# note for multiple of the same region
# the region id gets a number, i.e. barcode-1 barcode-2
- !Region
  region_id: barcode
  region_type: barcode
  name: Barcode
  sequence_type: onlist
  sequence: NNNNNNNNNNNNNNNN
  min_len: 16
  max_len: 16
  onlist: !Onlist
    filename: barcode_onlist.txt
    location: local
    md5: null
  regions:

# umi "Unique Molecular Identifier"
- !Region
  region_id: umi
  region_type: umi
  name: Unique Molecular Identifier
  sequence_type: random
  sequence: NNNNNNNNNN
  min_len: 10
  max_len: 10
  onlist:
  regions:

# cDNA "complementary DNA"
- !Region
  region_id: cDNA
  region_type: cDNA
  name: Complementary DNA
  sequence_type: random
  sequence: X
  min_len: 1
  max_len: 98
  onlist:
  regions:

# gDNA "genomic DNA"
- !Region
  region_id: gDNA
  region_type: gDNA
  name: Genomic DNA
  sequence_type: random
  sequence: X
  min_len: 1
  max_len: 98
  onlist:
  regions:
# Regions corresponding to FASTQ files are annotated a standard naming convention
# R1.fastq.gz "Read 1"
# R2.fastq.gz "Read 2"
# I1.fastq.gz "Index 1, i7 index"
# I2.fastq.gz "Index 2, i5 index"
```

# Contributing to Specification Improvements

## Introduction

This section outlines the process for suggesting improvements to the `seqspec` specification and the procedure for updating the specification.

## Suggesting Improvements

### How to Suggest

- **Open an Issue**: For suggesting improvements, please open a new issue in the GitHub repository.
- **Describe Your Suggestion**: Clearly describe the problem and your proposed solution. Include examples and use cases where possible.

### Community Discussion

- **Engagement**: Encourage community feedback on the suggestion through comments.
- **Iterate**: Be open to iterating on your suggestion based on community feedback.

## Review Process

### Steps for Review

1. **Initial Review**: A maintainer will review the suggestion for completeness and relevance.
2. **Community Feedback**: A period for community feedback will follow.
3. **Final Review**: The maintainers will make a final review, considering all feedback.

### Decision Making

- Decisions will be made based on the specification's goals, community feedback, and overall impact on the `seqspec` ecosystem.

## Updating the Specification

### Approval and Merging

- Once approved, a maintainer will merge the changes into the specification.
- Major changes may require a more detailed review process or a community vote.

### Versioning and Change Log

- **Versioning**: Follow semantic versioning. Major changes result in a version bump.
- **Change Log**: Update the change log with a summary of the changes and contributors.

### Testing and Validation

- Ensure any changes are tested for compatibility and do not break existing functionality.

## Conclusion

We value your contributions and aim to make the process of improving the specification collaborative and transparent. For any questions, please contact the repository maintainers.

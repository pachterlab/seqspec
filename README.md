# seqspec

`seqspec` is a machine-readable YAML file format for genomic library sequence and structure. It was inspired by and builds off of the Teichmann Lab [Single Cell Genomics Library Structure](https://github.com/Teichlab/scg_lib_structs) by [Xi Chen](https://github.com/dbrg77).

A list of `seqspec` examples for multiple assays can be found in the `assays/` folder. Each `spec.yaml` describes the 5'->3' "Final library structure" for the assay. Sequence specification files can be formatted with the `seqspec` command line tool.

```bash
# development
pip install git+https://github.com/IGVF/seqspec.git

# released
pip install seqspec

seqspec format --help
```

## TODO

- format check that every element in “order” is present in “regions”
- format verify presence of onlist files
- list onlist files
- specify in each assay which sequencer is being used (dictates which strand is sequenced)
- add `container_type` to assay, options are `well, cell, droplet`
- add `region_type` to each region, make the `region_type`s standardized (make region_id free form)
- `region_id` can now become the ordering of the regions
- add `strand` to each region which states the strand the region is ordered in
- add `sequencer` to assay

## Specification

Each assay is described by two objects: the `Assay` object and the `Region` object. A library is described by one `Assay` object and multiple (possibly nested) `Region` objects. The `Region` objects are grouped with a `join` operation and an `order` on the sub`Region`s specified. A simple (but not fully specified example) looks like the following:

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

## Naming `Regions`

For consistency across assays I suggest the following naming conventions for standard regions. Note that the `region_id` for all atomic regions should be unique.

```yaml
# Assay region
!Assay
name: My-RNA-Assay
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

## Contributing

Thank you for wanting to improve `seqspec`. If you have a bug that is related to `seqspec` please create an issue. The issue should contain

- the `seqspec` command ran,
- the error message, and
- the `seqspec` and python version.

If you'd like to add assays sequence specifications or make modifications to the `seqspec` tool please do the following:

1. Fork the project.

```
# Press "Fork" at the top right of the GitHub page
```

2. Clone the fork and create a branch for your feature

```bash
git clone https://github.com/<USERNAME>/seqspec.git
cd seqspec
git checkout -b cool-new-feature
```

3. Make changes, add files, and commit

```bash
# make changes, add files, and commit them
git add path/to/file1.yaml path/to/file2.yaml
git commit -m "I made these changes"
```

4. Push changes to GitHub

```bash
git push origin cool-new-feature
```

5. Submit a pull request

If you are unfamilar with pull requests, you can find more information on the [GitHub help page.](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests)

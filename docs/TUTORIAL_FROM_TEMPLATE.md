# Writing a seqspec file for a set of FASTQs
A seqspec file describes the library and read structure of a set of genomics data. Understanding both structures is crucial for analyzing sequencing reads. Even if the library construction process is unknown, a seqspec file can still be generated for a set of FASTQ reads.
## Example Dataset
We will generate a seqspec file for the following dataset:

```json
{
  "observation_id": "GSM3587010",
  "doi": "https://doi.org/10.1084/jem.20191130",
  "species": "homo sapiens",
  "organ": "colon",
  "name": "age 55 years old",
  "description": "epithelial cells",
  "technology": "10xv2",
  "links": [
    {
      "accession": "GSM3587010",
      "filename": "SRR8513796_1.fastq.gz",
      "filetype": null,
      "filesize": null,
      "md5": null,
      "urltype": "ftp",
      "url": "ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR851/006/SRR8513796/SRR8513796_1.fastq.gz"
    },
    {
      "accession": "GSM3587010",
      "filename": "SRR8513796_2.fastq.gz",
      "filetype": null,
      "filesize": null,
      "md5": null,
      "urltype": "ftp",
      "url": "ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR851/006/SRR8513796/SRR8513796_2.fastq.gz"
    }
  ]
}
```

    

The technology used is 10xv2. The read structure for 10xv2 libraries is:

• **R1.fastq.gz** (SRR8513796_1.fastq.gz): 16bp cell barcode followed by a 10bp UMI.
• **R2.fastq.gz** (SRR8513796_2.fastq.gz): cDNA, user-defined length.
• **Cell barcode onlist**: [Cell barcode list](https://github.com/pachterlab/qcbc/raw/main/tests/10xRNAv2/737K-august-2016.txt.gz).

The library was generated using the Illumina Hiseq X Ten platform with 150-bp paired-end reads.

## Download reads
First, download the FASTQ files and check the lengths of the reads:
```bash
# download the two FASTQ files
$ wget ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR851/006/SRR8513796/SRR8513796_1.fastq.gz
$ wget ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR851/006/SRR8513796/SRR8513796_2.fastq.gz

# view the first read in R1
$ zcat SRR8513796_1.fastq.gz | head -2
@SRR8513796.1 1/1
NGATTTCGTTGCGTTAATCATCGTCCTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTAAGAACCACATTATTATTTTGATAGATATAGAAATAGTCAAACCTAATCTACAAAAGTGCAGTATCATGCGGGGNCTTCGCAGCGTAGGTGTT

# count the number of bases in the R1 read
$ echo -n "NGATTTCGTTGCGTTAATCATCGTCCTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTAAGAACCACATTATTATTTTGATAGATATAGAAATAGTCAAACCTAATCTACAAAAGTGCAGTATCATGCGGGGNCTTCGCAGCGTAGGTGTT" | wc -c
150

# view the first read in R2
$ zcat SRR8513796_1.fastq.gz | head -2
@SRR8513796.1 1/2
NGAGTCTCCCTTCACCATTTCCGACGGCATCTATGGCTCAACATTTTTTGTAGCCACAGGCTTCCGCGGACTTCACGTCATTATTGGCTCAACTTTCGTCACTATCTGCTTTATCAGCCAACTAATATTTCACTTTACATACAAACATCA

# count the number of bases in the R2 read
$ echo -n "NGAGTCTCCCTTCACCATTTCCGACGGCATCTATGGCTCAACATTTTTTGTAGCCACAGGCTTCCGCGGACTTCACGTCATTATTGGCTCAACTTTCGTCACTATCTGCTTTATCAGCCAACTAATATTTCACTTTACATACAAACATCA" | wc -c
150
```

## Download template spec
Start with a template seqspec. The 10xv2 template can be found [here](https://github.com/pachterlab/seqspec/blob/main/examples/specs/template/10xv2-template.yml). Save this file as spec.yaml.

```yaml
!Assay
seqspec_version: 0.2.0
assay_id: 10xv2
name: 10xv2
doi: https://doi.org/10.1126/science.aam8999
date: 15 March 2018
description: 10x Genomics v2 single-cell rnaseq
modalities:
- rna
lib_struct: https://teichlab.github.io/scg_lib_structs/methods_html/10xChromium3.html
sequence_protocol: Not-specified
sequence_kit: Not-specified
library_protocol: 10xv2 RNA
library_kit: Not-specified
sequence_spec:
- !Read
  read_id: R1.fastq.gz
  name: Read 1
  modality: rna
  primer_id: r1_primer
  min_len: 26
  max_len: 26
  strand: pos
- !Read
  read_id: R2.fastq.gz
  name: Read 2
  modality: rna
  primer_id: r2_primer
  min_len: 150
  max_len: 150
  strand: neg
library_spec:
- !Region
  parent_id: null
  region_id: rna
  region_type: null
  name: null
  sequence_type: null
  sequence: AAAAAAAAAAAAAAAANNNNNNNNNNNNNNNNNNNNNNNNNNXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXAAAAAAAAAAAAAAAA
  min_len: 59
  max_len: 208
  onlist: null
  regions:
  - !Region
    parent_id: rna
    region_id: r1_primer
    region_type: r1_primer
    name: r1_primer
    sequence_type: fixed
    sequence: AAAAAAAAAAAAAAAA
    min_len: 16
    max_len: 16
    onlist: null
    regions: null
  - !Region
    parent_id: rna
    region_id: barcode
    region_type: barcode
    name: barcode
    sequence_type: onlist
    sequence: NNNNNNNNNNNNNNNN
    min_len: 16
    max_len: 16
    onlist: !Onlist
      location: remote
      filename: https://github.com/pachterlab/qcbc/raw/main/tests/10xRNAv2/737K-august-2016.txt.gz
      md5: 72aa64fd865bcda142c47d0da8370168
    regions: null
  - !Region
    parent_id: rna
    region_id: umi
    region_type: umi
    name: umi
    sequence_type: fixed
    sequence: NNNNNNNNNN
    min_len: 10
    max_len: 10
    onlist: null
    regions: null
  - !Region
    parent_id: rna
    region_id: cdna
    region_type: cdna
    name: cdna
    sequence_type: fixed
    sequence: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    min_len: 1
    max_len: 150
    onlist: null
    regions: null
  - !Region
    parent_id: rna
    region_id: r2_primer
    region_type: r2_primer
    name: r2_primer
    sequence_type: fixed
    sequence: AAAAAAAAAAAAAAAA
    min_len: 16
    max_len: 16
    onlist: null
    regions: null
```

## Modify `sequence_spec`
A seqspec file requires the user to specify the primer used to generate each of the sequencing reads. Since we may not know the exact primer used by the authors, we specify two generic primers (r1_primer generates R1.fastq.gz and r2_primer generates R2.fastq.gz). Then we fill in the relevant information for the `sequence_spec` using the reads and information we can obtain from the fastq files. Note that sequencing this library on a Hiseq generates R1 reads on the positive strand and R2 reads on the negative strand.

```yaml
sequence_spec:
- !Read
  read_id: SRR8513796_1.fastq.gz
  name: Read 1
  modality: rna
  primer_id: r1_primer
  min_len: 150
  max_len: 150
  strand: pos
- !Read
  read_id: SRR8513796_1.fastq.gz
  name: Read 2
  modality: rna
  primer_id: r2_primer
  min_len: 150
  max_len: 150
  strand: neg
```

## Modify `library_spec`
Ensure that the `library_spec` matches the 10xv2 structure:
- r1 primer
- barcode (with barcode onlist)
- umi
- cdna
- r2 primer
```yaml
  - !Region
    parent_id: rna
    region_id: r1_primer
    region_type: r1_primer
    name: r1_primer
    sequence_type: fixed
    sequence: AAAAAAAAAAAAAAAA
    min_len: 16
    max_len: 16
    onlist: null
    regions: null
  - !Region
    parent_id: rna
    region_id: barcode
    region_type: barcode
    name: barcode
    sequence_type: onlist
    sequence: NNNNNNNNNNNNNNNN
    min_len: 16
    max_len: 16
    onlist: !Onlist
      location: remote
      filename: https://github.com/pachterlab/qcbc/raw/main/tests/10xRNAv2/737K-august-2016.txt.gz
      md5: 72aa64fd865bcda142c47d0da8370168
    regions: null
  - !Region
    parent_id: rna
    region_id: umi
    region_type: umi
    name: umi
    sequence_type: fixed
    sequence: NNNNNNNNNN
    min_len: 10
    max_len: 10
    onlist: null
    regions: null
  - !Region
    parent_id: rna
    region_id: cdna
    region_type: cdna
    name: cdna
    sequence_type: fixed
    sequence: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    min_len: 1
    max_len: 150
    onlist: null
    regions: null
  - !Region
    parent_id: rna
    region_id: r2_primer
    region_type: r2_primer
    name: r2_primer
    sequence_type: fixed
    sequence: AAAAAAAAAAAAAAAA
    min_len: 16
    max_len: 16
    onlist: null
    regions: null
```

## Modify the metadata
Lastly, we update the metadata for the seqspec file
```yaml
!Assay
seqspec_version: 0.2.0
assay_id: 10xv2
name: 10xv2
doi: https://doi.org/10.1084/jem.20191130
date: 21 November 2019
description: 10x Genomics v2 single-cell rnaseq
modalities:
- rna
lib_struct: https://teichlab.github.io/scg_lib_structs/methods_html/10xChromium3.html
sequence_protocol: Not-specified
sequence_kit: Not-specified
library_protocol: 10xv2 RNA
library_kit: Not-specified
```

## Format, check, and print the spec
Use the seqspec command line utility to format, check, and view the seqspec file:

```bash
$ seqspec format -o spec.yaml spec.yaml
$ seqspec check spec.yaml
$ seqspec print spec.yaml
```

# Getting started

To create a `seqspec` file for your own data, start by identifying the relevant sequenced elements in your FASTQ files. For example

- `R1.fastq.gz` contains
  - 16bp barcode from a predefined "onlist"
  - 12bp umi randomly generated
- `R2.fastq.gz` contains
  - 150bp cDNA
- `I1.fastq.gz` contains
  - 8bp sample index from a predefined "onlist"

Then, "initialize" a `seqspec` file with `seqspec init` which takes in a [newick](https://en.wikipedia.org/wiki/Newick_format) formatted string that specifies the information above. For more information about initializing a `seqspec` file, please see the section on `Initializing a seqspec`.

```bash
seqspec init -n myassay -m 1 -o spec.yaml "(((barcode:16,umi:12)R1.fastq.gz,(cDNA:150)R2.fastq.gz,(index7:8)I1.fastq.gz)rna)"
```

Next, add relevant information to the spec by hand. For example, add the "onlist" for the `R1.fastq.gz` barcode:

```yaml
- !Region
  parent_id: null
  region_id: barcode
  region_type: barcode
  name: barcode
  sequence_type: onlist
  sequence: NNNNNNNNNNNNNNNN
  min_len: 16
  max_len: 16
  onlist:
    filename: onlist_barcode.txt
    md5: 131d3e81f7070402fa972d320f88449b
  regions: null
```

Update the `seqspec` file with `seqspec format`:

```bash
seqspec format -o fmt.yaml spec.yaml
```

And lastly, check that the spec is properly formatted and manually correct errors as needed:

```bash
seqspec check fmt.yaml
```

To view the "ordered tree" representation of the `seqspec`, run

```bash
seqspec print fmt.yaml
```

which prints

```bash
                                             ┌─'barcode:16'
                              ┌─R1.fastq.gz──┤
                              │              └─'umi:12'
────────────── ──rna──────────┤
                              ├─R2.fastq.gz─ ──'cDNA:150'
                              └─I1.fastq.gz─ ──'index7:8'
```

# Initializing a `seqspec`

To help users create a seqspec from their own data, the `seqspec` cli offers a simple tool `seqspec init` that autogenerates a `spec.yaml` from a string representation of the data. The input is a [newick file format](https://en.wikipedia.org/wiki/Newick_format) which naturally represents nested grouping of sequencing files and sequenced elements. By way of example, suppose we had the following sequencing data:

- `R1.fastq.gz` contains
  - 16bp barcode from a predefined "onlist"
  - 12bp umi randomly generated
- `R2.fastq.gz` contains
  - 150bp cDNA
- `I1.fastq.gz` contains
  - 8bp sample index from a predefined "onlist"

A compatible `newick` string would be

```bash
(((barcode:16,umi:12)R1.fastq.gz,(cDNA:150)R2.fastq.gz,(index7:8)I1.fastq.gz)rna)
```

Breaking the string we see the nested structure of the data

```bash
(
    (
        (
            barcode:16,
            umi:12
        )R1.fastq.gz,
        (
            cDNA:150
        )R2.fastq.gz,
        (
            index7:8
        )I1.fastq.gz
    )rna
)
```

Initializing a `seqspec` specification is as simple as

```bash
seqspec init -n myassay -m 1 -o spec.yaml "(((barcode:16,umi:12)R1.fastq.gz,(cDNA:150)R2.fastq.gz,(index7:8)I1.fastq.gz)rna)"
```

Note that the newick string must be enclosed in quotes.

# Example

We are going to walk through the process of writing a `seqspec` sequencing specification. We will

1. Download the GitHub repo
2. Initialize a `seqspec`
3. Populate the `seqs[ec]`
4. Create a Pull Request to merge

## Introduction

`seqspec` is a format (and command-line tool) that specifies the library structure of sequencing molecules. It is written as a [YAML](https://en.wikipedia.org/wiki/YAML) file. The basic idea underlying `seqspec` is that sequencing libraries contain molecules that conform to a "template" which can be prespecified. This template comprises multiple "Regions" which are simply stretches labelled of nucleotides. For example, suppose we had a sequencing library where the molecules consisted of two random synthetic barcodes. The "template" would look something like

```
NNNNNNNNNTCTTTCCCTACACGACGCTCTTCCGATCT
<Barcode><--------SyntheticSeq------->
```

## Regions

Regions of template molecules are encoded as "Regions" in our `seqspec`. Each "Region" has multiple parameters for annotated the specified sequence. The example above is comprised of two regions:

```yaml
- !Region
  region_id: Barcode1
  region_type: null
  name: Barcode 1
  sequence_type: random
  sequence: NNNNNNNNNN
  min_len: 10
  max_len: 10
  onlist: null
  regions: null
- !Region
  region_id: SyntheticSeq
  region_type: null
  name: Synthetic Seq
  sequence_type: fixed
  sequence: TCTTTCCCTACACGACGCTCTTCCGATCT
  min_len: 29
  max_len: 29
  onlist: null
  regions: null
```

# Nesting Regions

Regions can also contain Regions. Supposed that we wanted to annotate `Barcode1` and `SyntheticSeq` as being derived from the "read". Then we can group both of those Regions into "parent" Region under the "regions" parameter.

```yaml
- !Region
  region_id: read1
  region_type: null
  name: Read 1
  sequence_type: joined
  sequence: NNNNNNNNNTCTTTCCCTACACGACGCTCTTCCGATCT
  min_len: 39
  max_len: 39
  onlist: null
  regions:
    - !Region
      region_id: Barcode1
      region_type: null
      name: Barcode 1
      sequence_type: random
      sequence: NNNNNNNNNN
      min_len: 10
      max_len: 10
      onlist: null
      join: null
    - !Region
      region_id: SyntheticSeq
      region_type: null
      name: Synthetic Seq
      sequence_type: fixed
      sequence: TCTTTCCCTACACGACGCTCTTCCGATCT
      min_len: 29
      max_len: 29
      onlist: null
      join: null
```

To illustrate the mechanics of a `seqspec`, we will construct one for the [ISSAAC-seq assay](https://teichlab.github.io/scg_lib_structs/methods_html/ISSAAC-seq.html). ISSAAC-seq is a "multi-modal" assay for single-cell RNA-seq and chromatin-accessibility in the same cell. We'll start by copying the template and modifying information about the assay.

```yaml
!Assay
name: ISSAAC-seq
doi: https://doi.org/10.1038/s41592-022-01601-4
description: single-cell RNAseq and ATACseq
modalities: [RNA, ATAC]
lib_struct: https://teichlab.github.io/scg_lib_structs/methods_html/ISSAAC-seq.html
assay_spec:
```

Since the assay is "multi-modal" we specify two modalities "RNA" and "ATAC". These will be the first two "parent" regions in the "assay_spec" group:

```yaml
assay_spec:
  - !Region
    region_id: RNA
    name: RNA
    sequence_type: joined
    sequence:
    min_len:
    max_len:
    onlist:
    regions: ...
  - !Region
    region_id: ATAC
    name: ATAC
    sequence_type: joined
    sequence:
    min_len:
    max_len:
    onlist:
    regions: ...
```

We'll leave most parameters empty for since, they will get auto populated once we fill out the "atomic" regions and run the `seqspec` command line tool. Now we list out all of the possible RNA regions and all of the possible ATAC regions. Note that these names come from the "(8) Final library structure:" section from the Teichmann lab website for ISSAAC-seq and are listed in the 5'->3' order.

For the RNA:

```
1. Illumina P5,16 bp Barcode,
2. s5,
3. ME,
4. cDNA,
5. 10 bp UMI,
6. Truseq Read 2,
7. i7,
8. Illumina P7
```

For the ATAC

```
1. Illumina P5,
2. 16 bp Barcode,
3. s5,
4. ME,
5. gDNA,
6. ME,
7. s7,
8. i7,
9. Illumina P7
```

Now that we have the atomic Region names, we can simply start to create atomic "Region" objects as described above using `seqspec init`.

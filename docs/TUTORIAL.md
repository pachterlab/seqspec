
# Getting started

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

Next, add relevant information to the spec by hand- add information about the assay to the spec:

```yaml
!Assay
seqspec_version: 0.0.0
assay: My Assay
sequencer: My Sequencer
name: MyAssay/Myseq
doi: doi-to-assay-release.org
publication_date: 01 January 1970
description: My awesome assay
modalities:
  - RNA
lib_struct: www.link-to-lib-structs.com
assay_spec:
	...
```

and add information to the regions you've identified. For example, add the "onlist" for the `R1.fastq.gz` barcode:

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




# A worked example

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

## Nesting Regions

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
seqspec_version: 0.0.0
assay: ISSAAC-seq
sequencer: Illumina MiSeq
name: ISSAAC-seq/Miseq
doi: https://doi.org/10.1038/s41592-022-01601-4
description: single-cell RNAseq and ATACseq
modalities: [RNA, ATAC]
lib_struct: https://teichlab.github.io/scg_lib_structs/methods_html/ISSAAC-seq.html
assay_spec:
```

Since the assay is "multi-modal" we specify two modalities "RNA" and "ATAC". These will be the first two "parent" regions in the `assay_spec` group:

```yaml
assay_spec:
  - !Region
    region_id: RNA
    region_type: RNA
    name: RNA
    sequence_type: joined
    sequence:
    min_len:
    max_len:
    onlist:
    regions: 
	    ...
  - !Region
    region_id: ATAC
    region_type: ATAC
    name: ATAC
    sequence_type: joined
    sequence:
    min_len:
    max_len:
    onlist:
    regions: 
	    ...
```

We'll leave most parameters empty since they will get auto populated once we fill out the "atomic" regions and run the `seqspec` command line tool. Now we list out all of the possible RNA regions and all of the possible ATAC regions. Note that these names come from the "(8) Final library structure:" section from the Teichmann lab website for ISSAAC-seq and are listed in the 5'->3' order.

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

Now that we have the atomic Region names, we can simply start to create atomic "Region" objects as described above using `seqspec init` or the named regions identified in [SPECIFICATION.md](SPECIFICATION.md).

## Checking the correctness of the spec

The `seqspec` CLI comes with the capabilities to check the correctness of your `spec.yaml` against the formal specification. When running `seqspec check spec.yaml` you may find that your spec has numerous errors that will need to be corrected. The following are the kinds of errors you may encounter:

```bash
# The "assay" value was not specified in the spec
[error 1] None is not of type 'string' in spec['assay']

# The "modalities" are not using the controlled vocabulary
[error 2] 'Ribonucleic acid' is not one of ['rna', 'tag', 'protein', 'atac', 'crispr'] in spec['modalities'][0]

# The "region_type" is not using the controlled vocabulary
[error 3] 'link_1' is not one of ['atac', 'barcode', 'cdna', 'crispr', 'fastq', 'gdna', 'hic', 'illumina_p5', 'illumina_p7', 'index5', 'index7', 'linker', 'ME1', 'ME2', 'methyl', 'nextera_read1', 'nextera_read2', 'poly_A', 'poly_G', 'poly_T', 'poly_C', 'protein', 'rna', 's5', 's7', 'tag', 'truseq_read1', 'truseq_read2', 'umi'] in spec['assay_spec'][0]['regions'][3]['region_type']

# The "sequence_type" is not using the controlled vocabulary
[error 4] 'linker' is not one of ['fixed', 'random', 'onlist', 'joined'] in spec['assay_spec'][0]['regions'][3]['sequence_type']

# The "region_id" is not unique across the spec
[error 5] region_id 'cell_bc' is not unique across all regions

# The length of the given "sequence" is less than the "min_len" specified for the sequence
[error 6] 'sample_bc' sequence 'NNNNNNNN' length '8' is less than min_len '10'

# The "filename" for the specified "onlist" does not exist in the same location as the spec.
[error 7] i5_index_onlist.txt does not exist

# The provided "sequence" contains invalid characters (only A, C, G, T, N, and X are permitted)
[error 8] 'NNNNNNNNZN' does not match '^[ACGTNX]+$' in spec['assay_spec'][0]['regions'][4]['sequence']

# The "md5" for the given "onlist" file is not a valid md5sum
[error 9] '7asddd7asd7' does not match '^[a-f0-9]{32}$' in spec['assay_spec'][0]['regions'][8]['onlist']['md5']
```

`seqspec check spec.yaml` can be run again after fixing these errors to ensure that the spec fully conforms to the formal specification.

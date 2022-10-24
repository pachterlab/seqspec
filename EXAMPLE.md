# Writing a `seqspec`

We are going to walk through the process of writing a `seqspec` sequencing specification. We will
1. Download the GitHub repo
2. Create a copy of the `seqspec` template
3. Populate the template 
4. Create a Pull Request to merge 

# Introduction
`seqspec` is a format (and command-line tool) that specifies the library structure of sequencing molecules. It is written as a [YAML](https://en.wikipedia.org/wiki/YAML) file. The basic idea underlying `seqspec` is that sequencing libraries contain molecules that conform to a "template" which can be prespecified. This template comprises multiple "Regions" which are simply stretches labelled of nucleotides. For example, suppose we had a sequencing library where the molecules consisted of two random synthetic barcodes. The "template" would look something like

```
NNNNNNNNNTCTTTCCCTACACGACGCTCTTCCGATCT
<Barcode><--------SyntheticSeq------->
```
# Regions
Regions of template molecules are encoded as "Regions" in our `seqspec`. Each "Region" has multiple parameters for annotated the specified sequence. The example above is comprised of two regions:

```yaml
- !Region
  region_id: Barcode1
  name: Barcode 1
  sequence_type: random
  sequence: NNNNNNNNNN
  min_len: 10
  max_len: 10
  onlist: null
  join: null
- !Region
  region_id: SyntheticSeq
  name: Synthetic Seq
  sequence_type: fixed
  sequence: TCTTTCCCTACACGACGCTCTTCCGATCT
  min_len: 29
  max_len: 29
  onlist: null
  join: null
```
# "Join"ing Regions
Regions can also contain Regions. Supposed that we wanted to annotate `Barcode1` and `SyntheticSeq` as being derived from the "read". Then we can group both of those Regions into "parent" Region under the "join" parameter.

```yaml
- !Region
  region_id: read1
  name: Read 1
  sequence_type: joined
  sequence: NNNNNNNNNTCTTTCCCTACACGACGCTCTTCCGATCT
  min_len: 39
  max_len: 39
  onlist: null
  join: !Join
    how: union
    order: [Barcode1, SyntheticSeq]
   regions:
     - !Region
       region_id: Barcode1
       name: Barcode 1
       sequence_type: random
       sequence: NNNNNNNNNN
       min_len: 10
       max_len: 10
       onlist: null
       join: null
     - !Region
       region_id: SyntheticSeq
       name: Synthetic Seq
       sequence_type: fixed
       sequence: TCTTTCCCTACACGACGCTCTTCCGATCT
       min_len: 29
       max_len: 29
       onlist: null
       join: null
```

# Example
To illustrate the mechanics of a `seqspec`, we will construct one for the [ISSAAC-seq assay]( https://teichlab.github.io/scg_lib_structs/methods_html/ISSAAC-seq.html). ISSAAC-seq is a "multi-modal" assay for single-cell RNA-seq and chromatin-accessibility in the same cell. We'll start by copying the template and modifying information about the assay.

```yaml
!Assay
name: ISSAAC-seq
doi: https://doi.org/10.1038/s41592-022-01601-4
description: single-cell RNAseq and ATACseq
modalities: [RNA, ATAC]
lib_struct: https://teichlab.github.io/scg_lib_structs/methods_html/ISSAAC-seq.html
assay_spec:
...
```
Since the assay is "multi-modal" we specify two modalities "RNA" and "ATAC". These will be the first two "parent" regions in the "assay_spec" group:

```
assay_spec:
  - !Region
    region_id: RNA
    name: RNA
    sequence_type: joined
    sequence: 
    min_len: 
    max_len: 
    onlist: 
    join: !Join
      how: union
      order: []
      regions:
      ...
  - !Region
    region_id: ATAC
    name: ATAC
    sequence_type: joined
    sequence: 
    min_len: 
    max_len: 
    onlist: 
    join: !Join
      how: union
      order: []
      regions:
      ...
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

Now that we have the atomic Region names, we can simply start to create atomic "Region" objects as described above.

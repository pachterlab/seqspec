---
title: Tool options
date: 2024-09-11
authors:
  - name: A. Sina Booeshaghi
---

# Usage

The `seqspec` tool operates on `seqspec` files and

1. Facilitates the standardization of preprocessing steps across different assays,
2. Enables data management and tracking,
3. Simplifies the interpretation and reuse of sequencing data.

:::{important}
The `seqspec` specification is detailed in [here](SEQSPEC_FILE.md). Please review it before using and developing `seqspec` files; knowing the structure will help in understanding how to effectively use `seqspec`.
:::

`seqspec` consists of 13 subcommands:

```
usage: seqspec [-h] <CMD> ...

seqspec 0.3.0: A machine-readable file format for genomic library sequence and structure.

GitHub: https://github.com/pachterlab/seqspec
Documentation: https://pachterlab.github.io/seqspec/

positional arguments:
  <CMD>
    check     Validate seqspec file against specification
    find      Find objects in seqspec file
    file      List files present in seqspec file
    format    Autoformat seqspec file
    index     Identify position of elements in seqspec file
    info      Get information from seqspec file
    init      Generate a new seqspec file
    methods   Convert seqspec file into methods section
    modify    Modify attributes of various elements in seqspec file
    onlist    Get onlist file for elements in seqspec file
    print     Display the sequence and/or library structure from seqspec file
    split     Split seqspec file by modality
    version   Get seqspec tool version and seqspec file version

optional arguments:
  -h, --help  show this help message and exit
```

`seqspec` operates on `seqspec` compatible YAML files that follow the specification. All of the following examples will use the `seqspec` specification for the [DOGMAseq-DIG](https://doi.org/10.1186/s13059-022-02698-8) assay which can be found here: `seqspec/examples/specs/dogmaseq-dig/spec.yaml`.

:::{attention}
**IMPORTANT**: Many `seqspec` commands require that the specification be properly formatted and error-corrected. Errors in the spec can be found with `seqspec check` (see below for instructions). The spec can be properly formatted (or "filled in") with `seqspec format`. It is recommended to run `seqspec format` followed by `seqspec check` after writing a new `seqspec` (or correcting errors in an existing one).
:::

## `seqspec check`: Validate seqspec file against specification

Check that the `seqspec` file is correctly formatted and consistent with the [specification](https://github.com/IGVF/seqspec/blob/main/docs/SPECIFICATION.md).

```bash
seqspec check [-h] [-o OUT] yaml
```

- optionally, `-o OUT` can be used to write the output to a file.
- `yaml` corresponds to the `seqspec` file.

A list of possible errors are shown below:

```bash
# The "assay" value was not specified in the spec
[error 1] None is not of type 'string' in spec['assay']

# The "modalities" are not using the controlled vocabulary
[error 2] 'Ribonucleic acid' is not one of ['rna', 'tag', 'protein', 'atac', 'crispr'] in spec['modalities'][0]

# The "region_type" is not using the controlled vocabulary
[error 3] 'link_1' is not one of ['atac', 'barcode', 'cdna', 'crispr', 'fastq', 'gdna', 'hic', 'illumina_p5', 'illumina_p7', 'index5', 'index7', 'linker', 'ME1', 'ME2', 'methyl', 'nextera_read1', 'nextera_read2', 'poly_A', 'poly_G', 'poly_T', 'poly_C', 'protein', 'rna', 's5', 's7', 'tag', 'truseq_read1', 'truseq_read2', 'umi'] in spec['library_spec'][0]['regions'][3]['region_type']

# The "sequence_type" is not using the controlled vocabulary
[error 4] 'linker' is not one of ['fixed', 'random', 'onlist', 'joined'] in spec['library_spec'][0]['regions'][3]['sequence_type']

# The "region_id" is not unique across the spec
[error 5] region_id 'cell_bc' is not unique across all regions

# The length of the given "sequence" is less than the "min_len" specified for the sequence
[error 6] 'sample_bc' sequence 'NNNNNNNN' length '8' is less than min_len '10'

# The "filename" for the specified "onlist" does not exist in the same location as the spec.
[error 7] i5_index_onlist.txt does not exist

# The provided "sequence" contains invalid characters (only A, C, G, T, N, and X are permitted)
[error 8] 'NNNNNNNNZN' does not match '^[ACGTNX]+$' in spec['library_spec'][0]['regions'][4]['sequence']

# The "md5" for the given "onlist" file is not a valid md5sum
[error 9] '7asddd7asd7' does not match '^[a-f0-9]{32}$' in spec['library_spec'][0]['regions'][8]['onlist']['md5']
```

### Examples

```bash
# check the spec against the formal specification
$ seqspec check spec.yaml
[error 1] None is not of type 'string' in spec['assay']
[error 2] 'Ribonucleic acid' is not one of ['rna', 'tag', 'protein', 'atac', 'crispr'] in spec['modalities'][0]
```

## `seqspec find`: Find objects in seqspec file

```bash
seqspec find [-h] [-o OUT] [-s Selector] -m MODALITY [-i IDs] yaml
```

- optionally, `-o OUT` can be used to write the output to a file.
- optionally, `-s Selector` is the type of the ID you are searching for (default: region). Can be one of
  - read
  - region
  - file
  - region-type
- `-m MODALITY` is the modality in which you are searching within.
- `-i IDs` the ID you are searching for.
- `yaml` corresponds to the `seqspec` file.

### Examples

```bash
# Find reads by id
$ seqspec find -m rna -s read -i rna_R1 spec.yaml
- !Read
  read_id: rna_R1
  name: rna Read 1
  modality: rna
  primer_id: rna_truseq_read1
  min_len: 28
  max_len: 28
  strand: pos
  files:
  - !File
    file_id: rna_R1_SRR18677638.fastq.gz
    filename: rna_R1_SRR18677638.fastq.gz
    filetype: fastq
    filesize: 18499436
    url: fastqs/rna_R1_SRR18677638.fastq.gz
    urltype: local
    md5: 7eb15a70da9b729b5a87e30b6596b641

# Find regions with `barcode` region type
$ seqspec find -m rna -s region-type -i barcode spec.yaml
- !Region
  region_id: rna_cell_bc
  region_type: barcode
  name: Cell Barcode
  sequence_type: onlist
  sequence: NNNNNNNNNNNNNNNN
  min_len: 16
  max_len: 16
  onlist: !Onlist
    location: local
    filename: RNA-737K-arc-v1.txt
    filetype: txt
    filesize: 0
    url: RNA-737K-arc-v1.txt
    urltype: local
    md5: a88cd21e801ae6f9a7d9a48b67ccf693
    file_id: RNA-737K-arc-v1.txt
  regions: null
  parent_id: rna
```

## `seqspec file`: List files present in seqspec file

```bash
seqspec file [-h] [-o OUT] [-i IDs] -m MODALITY [-s SELECTOR] [-f FORMAT] [-k KEY] yaml
```

- optionally, `-o OUT` can be used to write the output to a file.
- optionally, `-s Selector` is the type of the ID you are searching for (default: read). Can be one of
  - read
  - region
  - file
  - region-type
- optionally, `-f FORMAT` is the format to return the list of files. Can be one of
  - paired
  - interleaved
  - index
  - list
  - json
- optionally, `-k KEY` is the key to display for the file (default: file_id). Can be one of
  - file_id
  - filename
  - filetype
  - filesize
  - url
  - urltype
  - md5
  - all
- `-m MODALITY` is the modality in which you are searching within.
- `-i IDs` the ID you are searching for.
- `yaml` corresponds to the `seqspec` file.

### Examples

```bash
# List paired read files
$ seqspec file -m rna spec.yaml
rna_R1_SRR18677638.fastq.gz     rna_R2_SRR18677638.fastq.gz

# List interleaved read files
$ seqspec file -m rna -f interleaved spec.yaml
rna_R1_SRR18677638.fastq.gz
rna_R2_SRR18677638.fastq.gz

# List urls of all read files
$ seqspec file -m rna -f list -k url spec.yaml
rna_R1  rna_R1_SRR18677638.fastq.gz     fastqs/rna_R1_SRR18677638.fastq.gz
rna_R2  rna_R2_SRR18677638.fastq.gz     fastqs/rna_R2_SRR18677638.fastq.gz

# List all files in regions
$ seqspec file -m rna -f list -s region -k all spec.yaml
rna_cell_bc     RNA-737K-arc-v1.txt     RNA-737K-arc-v1.txt     txt     2142553 https://github.com/pachterlab/qcbc/raw/main/tests/10xMOME/RNA-737K-arc-v1.txt.gz        https   a88cd21e801ae6f9a7d9a48b67ccf693

# List files for barcode regions in json
$ seqspec file -m rna -f json -s region-type -k all -i barcode spec.yaml
[
    {
        "file_id": "RNA-737K-arc-v1.txt",
        "filename": "RNA-737K-arc-v1.txt",
        "filetype": "txt",
        "filesize": 2142553,
        "url": "https://github.com/pachterlab/qcbc/raw/main/tests/10xMOME/RNA-737K-arc-v1.txt.gz",
        "urltype": "https",
        "md5": "a88cd21e801ae6f9a7d9a48b67ccf693"
    }
]
```

Note: `seqspec file -s read` gets the files for the read, not the files contained in the regions mapped to the read.

## `seqspec format`: Autoformat seqspec file

Automatically fill in missing fields in the spec.

```bash
seqspec format [-h] [-o OUT] yaml
```

- `-o OUT` the path to create the formatted `seqspec` file.
- `yaml` corresponds to the `seqspec` file.

### Examples

```bash
# format the spec and print the spec to stdout
$ seqspec format spec.yaml

# note you can also overwrite the spec you are formatting
$ seqspec format -o spec.yaml spec.yaml
```

## `seqspec index`: Identify position of elements in seqspec file

Identify the position of elements in a spec for use in downstream tools. Returns the 0-indexed position of elements contained in a given region in the 5'->3' direction.

```
seqspec index [-o OUT] [-t TOOL] [--rev] -m MODALITY -r REGION yaml
seqspec index [-h] [-o OUT] [-t TOOL] [-s SELECTOR] [--rev] -m MODALITY [-i IDs] yaml
```

- optionally, `-o OUT` can be used to write the output to a file.
- optionally, `--rev` can be set to return the 3'->5' index.
- optionally, `-t TOOL` returns the indices in the format specified by the tool. One of:
  - `kb`: `kallisto`/`kb count` `-x TECHNOLOGY` ([format](https://pachterlab.github.io/kallisto/manual#:~:text=will%20accept%20a-,string,-specifying%20a%20new)) requires a barcode, UMI, and sequence. The following `region_type` are used during indexing:
    - `barcode` for the barcode
    - `umi` for the umi
    - `cdna`, `gdna`, `protein`, or `tag` for the sequence
  - `seqkit`: `seqkit subseq` `-r, --region string` ([format](https://bioinf.shenwei.me/seqkit/usage/#subseq))
  - `simpleaf`: `simpleaf quant` `-c, --chemistry` ([format](https://simpleaf.readthedocs.io/en/latest/quant-command.html#a-note-on-the-chemistry-flag)) requires a barcode, UMI, and sequence. The following `region_type` are used during indexing:
    - `barcode` for the barcode
    - `umi` for the umi
    - `cdna` for the sequence
  - `starsolo`: `--soloCBstart`, `--soloCBlen`, `--soloUMIstart`, `--soloUMIlen` ([format](https://github.com/alexdobin/STAR/blob/master/docs/STARsolo.md#barcode-geometry)) requires a barcode, UMI, and sequence. The following `region_type` are used during indexing:
    - `barcode` for the barcode
    - `umi` for the umi
    - `cdna` for the sequence
  - `tab`: tab delimited file (`region<\t>element<\t>start<t>end`)
  - `zumis`: yaml ([format](https://github.com/sdparekh/zUMIs/blob/main/zUMIs.yaml)) requires a barcode, UMI, and sequence. The following `region_type` are used during indexing:
    - `barcode` for the barcode
    - `umi` for the umi
    - `cdna` for the sequence
- optionally, `-s Selector` is the type of the ID you are searching for (default: read). Can be one of
  - read
  - region
  - file
- `-m MODALITY` is the modality that the `-r REGION`region resides in.
- `-i IDs` is the ID of the object you are indexing.
- `yaml` corresponds to the `seqspec` file.

### Examples

```bash
# get the indices of the elements contained within the FASTQs specified in the spec in tab format
$ seqspec index -m atac -s file -i atac_R1_SRR18677642.fastq.gz,atac_R2_SRR18677642.fastq.gz,atac_R3_SRR18677642.fastq.gz spec.yaml
atac_R1 gdna    gdna    0       53
atac_R2 atac linker     linker  0       8
atac_R2 Cell Barcode    barcode 8       24
atac_R3 gdna    gdna    0       53

# do the same but in the kb format
$ seqspec index -m atac -t kb -s file -i atac_R1_SRR18677642.fastq.gz,atac_R2_SRR18677642.fastq.gz,atac_R3_SRR18677642.fastq.gz spec.yaml
1,8,24:-1,-1,-1:0,0,53,2,0,53

# If the files are specified in the spec then -i can be omitted
$ seqspec index -m atac -t kb -s file spec.yaml
1,8,24:-1,-1,-1:0,0,53,2,0,53
```

## `seqspec info`: get info about seqspec file

```bash
seqspec info [-h] [-k KEY] [-f FORMAT] [-o OUT] yaml
```

- optionally, `-o OUT` path to write the info.
- optionally, `-k KEY` the object to display (default: meta). Can be one of
  - modalities
  - meta
  - seqeunce_spec
  - library_spec
- optionally, `-f FORMAT` the output format (default: tab). Can be one of
  - tab
  - json
- `yaml` corresponds to the `seqspec` file.

### Examples

```bash
# Get meta information in json format
$ seqspec info -f json spec.yaml
{
    "seqspec_version": "0.3.0",
    "assay_id": "DOGMAseq-DIG",
    "name": "DOGMAseq-DIG/Illumina",
    "doi": "https://doi.org/10.1186/s13059-022-02698-8",
    "date": "23 June 2022",
    "description": "DOGMAseq with digitonin (DIG) is a single-cell multi-omics assay that simultaneously measures protein, RNA, and chromatin accessibility in single cells. The assay is based on the DOGMAseq technology, which uses a DNA-barcoded antibody library to capture proteins of interest, followed by a single-cell RNA-seq protocol and a single-cell ATAC-seq protocol. The DOGMAseq-LLL assay is designed to be compatible with the 10x Genomics Chromium platform.",
    "lib_struct": "",
    ...
    # long output omitted

# Get the list of modalities
$ seqspec info -k modalities spec.yaml
protein tag     rna     atac

# Get library spec in json format
$ seqspec info -f json -k library_spec spec.yaml
{
    "protein": [
        {
            "region_id": "ghost_protein_truseq_read1",
            "region_type": "named",
            "name": "Truseq Read 1",
            "sequence_type": "fixed",
            "onlist": null,
            "sequence": "",
            "min_len": 0,
            "max_len": 0,
            "regions": []
        },
        ...
        # long output omitted

# Get sequence spec in json format
$ seqspec info -f json -k sequence_spec spec.yaml
[
    {
        "read_id": "protein_R1",
        "name": "protein Read 1",
        "modality": "protein",
        "primer_id": "protein_truseq_read1",
        "min_len": 28,
        "max_len": 28,
        "strand": "pos",
        "files": [
        ...
        # long output omitted
```

## `seqspec init`: Generate a new seqspec file

```bash
seqspec init [-h] -n NAME -m MODALITIES -r READS [-o OUT] newick
```

- optionally, `-o OUT` path to create `seqspec` file.
- `-m MODALITIES` is a comma-separated list of modalities (e.g. rna,atac)
- `-n NAME` is the name associated with the `seqspec` file.
- `r READS ` is a list of modalities, reads, primer_ids, lengths, and strand (e.g. modality,fastq_name,primer_id,len,strand:...) one for each "Read"
- `newick` is the [`newick`](http://bioinformatics.intec.ugent.be/MotifSuite/treeformat.php#:~:text=Newick%20Tree%20file%20format,html.) string corresponding to the structure of library molecule.

### Examples

```bash
# single-cell RNA
# 16bp barcode + 12bp UMI (in r1.fastq.gz) and 150bp cdna (in r2.fastq.gz)
$ seqspec init -n myassay -m rna -o spec.yaml -r rna,R1.fastq.gz,r1_primer,26,pos:rna,R2.fastq.gz,r2_primer,100,neg "((r1_primer:0,barcode:16,umi:12,cdna:150,r2_primer:0)rna)"

# single-cell multiome ATAC + RNA
# RNA Modality: 16bp barcode + 12bp UMI (in rna_r1.fastq.gz) and 150bp cdna (in rna_r2.fastq.gz)
# ATAC Modality: 16bp barcode (in atac_r1.fastq.gz) + 150bp gdna (in atac_r2.fastq.gz) + 150bp gdna (in atac_r3.fastq.gz)
$ seqspec init -n myassay -m rna,atac -o spec.yaml -r rna,rna_R1.fastq.gz,rna_r1_primer,26,pos:rna,rna_R2.fastq.gz,rna_r2_primer,100,neg:atac,atac_R1.fastq.gz,atac_r1_primer,100,pos:atac,atac_R2.fastq.gz,atac_r1_primer,16,neg:atac,atac_R3.fastq.gz,atac_r2_primer,100,neg "(((rna_r1_primer:0,barcode:16,umi:12,cdna:150,rna_r2_primer:0)rna),(barcode:16,atac_r1_primer:1,gdna:150,atac_r2_primer)atac)"
```

## `seqsoec methods`: Convert seqspec file into methods section

Generate a methods section from a seqspec file.

```bash
seqspec methods [-h] -m MODALITY [-o OUT] yaml
```

- optionally, `-o OUT` path to write the methods section.
- `-m MODALITY` is the modality to write the methods for.
- `yaml` corresponds to the `seqspec` file.

### Examples

```bash
# print methods for rna modality
$ seqspec methods -m rna spec.yaml
Methods
The rna portion of the DOGMAseq-DIG/Illumina assay was generated on 23 June 2022.

Libary structure

The library was generated using the CG000338 Chromium Next GEM Multiome ATAC + Gene Expression Rev. D protocol (10x Genomics) library protocol and Illumina Truseq Single Index library kit. The library contains the following elements:

1. Truseq Read 1: 33-33bp fixed sequence (ACACTCTTTCCCTACACGACGCTCTTCCGATCT).
2. Cell Barcode: 16-16bp onlist sequence (NNNNNNNNNNNNNNNN), onlist file: RNA-737K-arc-v1.txt.
3. umi: 12-12bp random sequence (XXXXXXXXXXXX).
4. cdna: 102-102bp random sequence (XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX).
5. Truseq Read 2: 34-34bp fixed sequence (AGATCGGAAGAGCACACGTCTGAACTCCAGTCAC).


Sequence structure

The library was sequenced on a Illumina NovaSeq 6000 (EFO:0008637) using the NovaSeq 6000 S2 Reagent Kit v1.5 (100 cycles) sequencing kit. The library was sequenced using the following configuration:

- rna Read 1: 28 cycles on the positive strand using the rna_truseq_read1 primer. The following files contain the sequences in Read 1:
  - File 1: rna_R1_SRR18677638.fastq.gz
- rna Read 2: 102 cycles on the negative strand using the rna_truseq_read2 primer. The following files contain the sequences in Read 2:
  - File 1: rna_R2_SRR18677638.fastq.gz
```

## `seqspec modify`: Modify attributes of various elements in seqspec file

```bash
seqspec modify [-h] [--read-id READID] [--read-name READNAME] [--primer-id PRIMERID] [--strand STRAND] [--files FILES] [--region-id REGIONID] [--region-type REGIONTYPE] [--region-name REGIONNAME] [--sequence-type SEQUENCETYPE] [--sequence SEQUENCE] [--min-len MINLEN] [--max-len MAXLEN] [-o OUT] [-i IDs] [-s SELECTOR] -m MODALITY yaml
```

Read modifications

- optionally, `--read-id READID` specifies the new `read_id`.
- optionally, `--read-name READNAME` specifies the new `name`.
- optionally, `--primer-id PRIMERID` specifies the new `primer_id`.
- optionally, `--strand STRAND` specifies the new `strand`.
- optionally, `--files FILES` files to insert into a read (format filename,filetype,filesize,url,urltype,md5:...)

Region modifications

- optionally, `--region-id REGIONID` specifies the new `region_id`.
- optionally, `--region-type REGIONTYPE` specifies the new `region_type`, must come from controlled vocabulary.
- optionally, `--region-name REGIONNAME` specifies the new name for the region.
- optionally, `--sequence-type SEQUENCETYPE` specifies the new sequence type, must come from the controlled vocabulary.
- optionally, `--sequence SEQUENCE` specifies the new sequence for the region.

Read or region modifications

- optionally, `--min-len MINLEN` sets the new minimum length that the sequence should have.
- optionally, `--max-len MAXLEN` sets the new maximum length that the sequence can have.

- `-o OUT` path to create or overwrite the `seqspec` file.
- `-i ID` is the `id` of the object to modify.
- `-s SELECTOR` is the type of the `id` of the object to modify (default: read). Can be one of:
  - read
  - region
- `-m MODALITY` is the `modality` containing the `region_id` you are modifying.
- `yaml` corresponds to the `seqspec` file.

_Note_: modifying multiple attributes at one time is currently not supported.

### Examples

```bash
# modify the read id
$ seqspec modify -m atac -o mod_spec.yaml -i atac_R1 --read-id renamed_atac_R1 spec.yaml

# modify the region id
$ seqspec modify -m atac -o mod_spec.yaml -s region -i atac_cell_bc --region-id renamed_atac_cell_bc spec.yaml

# modify the files for R1 fastq
$ seqspec modify -m atac -o mod_spec.yaml -i atac_R1 --files "R1_1.fastq.gz,fastq,0,./fastq/R1_1.fastq.gz,local,null:R1_2.fastq.gz,fastq,0,./fastq/R1_2.fastq.gz,local,null" spec.yaml
```

## `seqspec onlist`: Get onlist file for elements in seqspec file

```bash
seqspec onlist [-h] [-o OUT] [-s SELECTOR] [-f FORMAT] [-i IDs] -m MODALITY yaml
```

- optionally, `-o OUT` to set the path of the onlist file.
- `-m MODALITY` is the modality in which you are searching for the region.
- `-i ID` is the `id` of the object to search for the onlist.
- `-s SELECTOR` is the type of the `id` of the object (default: read). Can be one of:
  - read
  - region
  - region-type
- `-f FORMAT` is the format for combining multiple onlists (default: product). Can be one of:
  - product (cartesian product)
  - multi
- `yaml` corresponds to the `seqspec` file.

_Note_: If, for example, there are multiple regions with the specified `region_type` in the modality (e.g. multiple barcodes), then `seqspec onlist` will return a path to an onlist that it generates where the entries in that onlist are the cartesian product of the onlists for all of the regions found.

### Examples

```bash
# Get onlist for the element in the rna_R1 read
$ seqspec onlist -m rna -s read -i rna_R1 spec.yaml
/path/to/spec/folder/RNA-737K-arc-v1.txt

# Get onlist for barcode region type
$ seqspec onlist -m rna -s region-type -i barcode spec.yaml
/path/to/spec/folder/RNA-737K-arc-v1.txt
```

## `seqspec print`: Display the sequence and/or library structure from seqspec file

Print sequence and/or library structure as ascii, png, or html.

```bash
seqspec print [-h] [-o OUT] [-f FORMAT] yaml
```

- optionally, `-o OUT` to set the path of printed file.
- optionally, `-f FORMAT` is the format of the printed file. Can be one of:
  - `library-ascii`: prints an ascii tree of the library_spec
  - `seqspec-html`: prints an html of both the library_spec and sequence_spec (TODO this is incomplete)
  - `seqspec-png`: prints an png of both the library_spec and sequence_spec (TODO this is incomplete)
  - `seqspec-ascii`: prints an ascii representation of both the library_spec and sequence_spec
- `yaml` corresponds to the `seqspec` file.

### Examples

```bash
# Print the library structure as ascii
$ seqspec print spec.yaml
           ┌─'ghost_protein_truseq_read1:0'
           ├─'protein_truseq_read1:33'
           ├─'protein_cell_bc:16'
 ┌─protein─┤
 │         ├─'protein_umi:12'
 │         ├─'protein_seq:15'
 │         └─'protein_truseq_read2:34'
 │         ┌─'tag_truseq_read1:33'
 │         ├─'tag_cell_bc:16'
 ├─tag─────┼─'tag_umi:12'
 │         ├─'tag_seq:15'
─┤         └─'tag_truseq_read2:34'
 │         ┌─'rna_truseq_read1:33'
 │         ├─'rna_cell_bc:16'
 ├─rna─────┼─'rna_umi:12'
 │         ├─'cdna:102'
 │         └─'rna_truseq_read2:34'
 │         ┌─'atac_truseq_read1:33'
 │         ├─'gDNA:100'
 └─atac────┼─'atac_truseq_read2:34'
           ├─'spacer:8'
           └─'atac_cell_bc:16'

# Print the sequence and library structure as ascii
$ seqspec print -f seqspec-ascii spec.yaml
protein
---
                                |--------------------------->(1) protein_R1
ACACTCTTTCCCTACACGACGCTCTTCCGATCTNNNNNNNNNNNNNNNNXXXXXXXXXXXXXXXXXXXXXXXXXXXAGATCGGAAGAGCACACGTCTGAACTCCAGTCAC
TGTGAGAAAGGGATGTGCTGCGAGAAGGCTAGANNNNNNNNNNNNNNNNXXXXXXXXXXXXXXXXXXXXXXXXXXXTCTAGCCTTCTCGTGTGCAGACTTGAGGTCAGTG
                                                             <--------------|(2) protein_R2
tag
---
                                |--------------------------->(1) tag_R1
ACACTCTTTCCCTACACGACGCTCTTCCGATCTNNNNNNNNNNNNNNNNXXXXXXXXXXXXXXXXXXXXXXXXXXXAGATCGGAAGAGCACACGTCTGAACTCCAGTCAC
TGTGAGAAAGGGATGTGCTGCGAGAAGGCTAGANNNNNNNNNNNNNNNNXXXXXXXXXXXXXXXXXXXXXXXXXXXTCTAGCCTTCTCGTGTGCAGACTTGAGGTCAGTG
                                                             <--------------|(2) tag_R2
rna
---
                                |--------------------------->(1) rna_R1
ACACTCTTTCCCTACACGACGCTCTTCCGATCTNNNNNNNNNNNNNNNNXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXAGATCGGAAGAGCACACGTCTGAACTCCAGTCAC
TGTGAGAAAGGGATGTGCTGCGAGAAGGCTAGANNNNNNNNNNNNNNNNXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXTCTAGCCTTCTCGTGTGCAGACTTGAGGTCAGTG
                                                             <-----------------------------------------------------------------------------------------------------|(2) rna_R2
atac
---
                                |---------------------------------------------------->(1) atac_R1
                                                                                                                                                                      |----------------------->(2) atac_R2
ACACTCTTTCCCTACACGACGCTCTTCCGATCTXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXAGATCGGAAGAGCACACGTCTGAACTCCAGTCACCAGACGCGNNNNNNNNNNNNNNNN
TGTGAGAAAGGGATGTGCTGCGAGAAGGCTAGAXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXTCTAGCCTTCTCGTGTGCAGACTTGAGGTCAGTGGTCTGCGCNNNNNNNNNNNNNNNN
                                                                                <----------------------------------------------------|(3) atac_R3


# Print the sequence and library structure as html
$ seqspec print -f seqspec-html spec.yaml
  <!DOCTYPE html>
  <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <style>
      highlight {
      color: green;
      }
      ...
      # long output omitted

# Print the library structure as a png
$ seqspec print -o spec.png -f seqspec-png spec.yaml
```

## `seqspec split`: Split seqspec file by modality

```bash
seqspec split [-h] -o OUT yaml
```

- optionally, `-o OUT` name prepended to split specs.
- `yaml` corresponds to the `seqspec` file.

### Examples

```bash
# split spec into modalities
$ seqspec split -o split spec.yaml
$ ls -1
spec.yaml
split.atac.yaml
split.protein.yaml
split.rna.yaml
split.tag.yaml
```

## `seqspec version`: Get seqspec tool version and seqspec file version

```bash
seqspec version [-h] [-o OUT] yaml
```

- optionally, `-o OUT` path to file to write output.
- `yaml` corresponds to the `seqspec` file.

### Examples

```bash
# Get versions of tool and file
$ seqspec version spec.yaml
seqspec version: 0.3.0
seqspec file version: 0.3.0
```

## (HIDDEN) `seqspec upgrade`: Upgrade seqspec file from older versions to the current version

This is a hidden subcommand that upgrades an old version of the spec to the current one. It is not intended to be used in a production environment.

```bash
seqspec upgrade [-h] [-o OUT] yaml
```

### Examples

```bash
# upgrade spec
$ seqspec upgrade -o spec.yaml spec.yaml
```

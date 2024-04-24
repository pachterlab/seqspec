## Installation

The development version can be installed with

```bash
pip install git+https://github.com/pachterlab/seqspec
```

## Usage

The `seqspec` specification is detailed in `docs/SPECIFICATION.md`. Please review it before using and developing `seqspec` files; knowing the structure will help in understanding how to effectively use `seqspec`.

`seqspec` consists of twelve subcommands:

```
$ seqspec
usage: seqspec [-h] <CMD> ...

seqspec 0.2.0: Format sequence specification files

positional arguments:
  <CMD>
    check     validate seqspec file
    find      find regions in a seqspec file
    format    format seqspec file
    genbank   get genbank about seqspec file
    index     index reads or regions in a seqspec file
    info      get info about seqspec file
    init      init a seqspec file
    modify    modify region attributes
    onlist    get onlist file for specific regions
    print     print seqspec file
    split     split seqspec into modalities
    version   Get seqspec version and seqspec file version

optional arguments:
  -h, --help  show this help message and exit
```

`seqspec` operates on `seqspec` compatible YAML files that follow the specification. All of the following examples will use the `seqspec` specification for the DOGMAseq-DIG assay which can be found here: `seqspec/examples/specs/dogmaseq-dig/spec.yaml`.

**IMPORTANT**: Many `seqspec` commands require that the specification be properly formatted and error-corrected. Errors in the spec can be found with `seqspec check` (see below for instructions). The spec can be properly formatted (or "filled in") with `seqspec format`. It is recommended to run `seqspec format` followed by `seqspec check` after writing a `seqspec` (or correcting errors in one).

### `seqspec check`: validate seqspec file

Check that the `seqspec` file is correctly formatted and consistent with the [specification](https://github.com/IGVF/seqspec/blob/main/docs/SPECIFICATION.md).

```
seqspec check [-o OUT] yaml
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

#### Examples

```bash
# check the spec against the formal specification
$ seqspec check spec.yaml
[error 1] None is not of type 'string' in spec['assay']
[error 2] 'Ribonucleic acid' is not one of ['rna', 'tag', 'protein', 'atac', 'crispr'] in spec['modalities'][0]
```

### `seqspec find`: find regions in a seqspec file

```
seqspec find [-o OUT] [--rtype] -m MODALITY -r REGION  yaml
```

- optionally, `-o OUT` can be used to write the output to a file.
- optionally, `--rtype` is set to search by `region_type` (where `-r` is from`region_type` vocabulary)
- `-m MODALITY` is the modality in which you are searching for the region.
- `-r REGION` is the `region_id` you are searching for.
- `yaml` corresponds to the `seqspec` file.

#### Examples

```bash
$ seqspec find -m rna -r barcode --rtype spec.yaml
- !Region
  region_id: rna_cell_bc
  region_type: barcode
  name: Cell Barcode
  sequence_type: onlist
  sequence: NNNNNNNNNNNNNNNN
  min_len: 16
  max_len: 16
  onlist: !Onlist
    filename: RNA-737K-arc-v1.txt
    md5: a88cd21e801ae6f9a7d9a48b67ccf693
  regions: null
  parent_id: rna_R1_SRR18677638.fastq.gz
```

### `seqspec format`: format seqspec file

```
seqspec format -o OUT yaml
```

- `-o OUT` the path to create the formatted `seqspec` file.
- `yaml` corresponds to the `seqspec` file.

#### Examples

```bash
# format the spec into a file called fmt.yaml
$ seqspec format -o fmt.yaml spec.yaml

# note you can also overwrite the spec you are formatting
$ seqspec format -o spec.yaml spec.yaml
```

### `seqspec index`: index regions in a seqspec file

Returns the 0-indexed position of elements contained in a given region in the 5'->3' direction.

```
seqspec index [-o OUT] [-t TOOL] [--rev] -m MODALITY -r REGION yaml
```

- optionally, `-o OUT` can be used to write the output to a file.
- optionally, `--rev` can be set to return the 3'->5' index.
- optionally, `-t TOOL` returns the indices in the format specified by the tool. One of:
  - `kb`: `kallisto`/`kb count` `-x TECHNOLOGY` ([format](https://pachterlab.github.io/kallisto/manual#:~:text=will%20accept%20a-,string,-specifying%20a%20new))
  - `seqkit`: `seqkit subseq` `-r, --region string` ([format](https://bioinf.shenwei.me/seqkit/usage/#subseq))
  - `simpleaf`: `simpleaf quant` `-c, --chemistry` ([format](https://simpleaf.readthedocs.io/en/latest/quant-command.html#a-note-on-the-chemistry-flag))
  - `starsolo`: `--soloCBstart`, `--soloCBlen`, `--soloUMIstart`, `--soloUMIlen` ([format](https://github.com/alexdobin/STAR/blob/master/docs/STARsolo.md#barcode-geometry)
  - `tab`: tab delimited file (`region<\t>element<\t>start<t>end`)
  - `zumis`: yaml ([format](https://github.com/sdparekh/zUMIs/blob/main/zUMIs.yaml))
- `-m MODALITY` is the modality that the `-r REGION`region resides in.
- `-r REGION` is the `region_id` you are indexing.
- `yaml` corresponds to the `seqspec` file.

#### Examples

```bash
# get the indices of the elements contained within the FASTQs specified in the spec in tab format
$ seqspec index -m atac -r fastqs/atac_R1_SRR18677642.fastq.gz,fastqs/atac_R2_SRR18677642.fastq.gz,fastqs/atac_R3_SRR18677642.fastq.gz  spec.yaml
atac_R1_SRR18677642.fastq.gz	gdna	0	52
atac_R2_SRR18677642.fastq.gz	linker	0	8
atac_R2_SRR18677642.fastq.gz	barcode	8	24
atac_R3_SRR18677642.fastq.gz	gdna	0	52

# do the same but in the kb format
$ seqspec index -t kb -m atac -r fastqs/atac_R1_SRR18677642.fastq.gz,fastqs/atac_R2_SRR18677642.fastq.gz,fastqs/atac_R3_SRR18677642.fastq.gz  spec.yaml
1,8,24:-1,-1,-1:0,0,52,2,0,52
```

### `seqspec info`: get info about seqspec file

```bash
seqspec info -o OUT yaml
```

- optionally, `-o OUT` path to create info json file.
- `yaml` corresponds to the `seqspec` file.

#### Examples

```bash
$ seqspec info spec.yaml
{
    "seqspec_version": "0.0.0",
    "assay": "DOGMAseq-DIG",
    "sequencer": "Illumina NovaSeq 6000 (S2 Reagent Kit v1.5)",
    "name": "DOGMAseq-DIG/Illumina",
    "doi": "https://doi.org/10.1186/s13059-022-02698-8",
    "publication_date": "23 June 2022",
    "description": "DOGMAseq with digitonin (DIG) is a single-cell multi-omics assay that simultaneously measures protein, RNA, and chromatin accessibility in single cells. The assay is based on the DOGMAseq technology, which uses a DNA-barcoded antibody library to capture proteins of interest, followed by a single-cell RNA-seq protocol and a single-cell ATAC-seq protocol. The DOGMAseq-LLL assay is designed to be compatible with the 10x Genomics Chromium platform.",
    "modalities": [
        "protein",
        "tag",
        "rna",
        "atac"
    ],
    "lib_struct": ""
}
```

### `seqspec init`: init a seqspec file

```bash
seqspec init -n NAME -m MODALITIES -o OUT newick
```

- `-o OUT` path to create `seqspec` file.
- `-m MODALITIES` is the number of modalities to create in the `seqspec` file.
- `-n NAME` is the name associated with the `seqspec` file.
- `newick` is the [`newick`](http://bioinformatics.intec.ugent.be/MotifSuite/treeformat.php#:~:text=Newick%20Tree%20file%20format,html.) string corresponding to the structure of assay.

#### Examples

```bash
# single-cell RNA
# 16bp barcode + 12bp UMI (in r1.fastq.gz) and 150bp cdna (in r2.fastq.gz)
$ seqspec init -n myassay -m 1 -o spec.yaml "(((barcode:16,umi:12)r1.fastq.gz,(cdna:150)r2.fastq.gz)rna)"

# single-cell ATAC + RNA
# RNA Modality: 16bp barcode + 12bp UMI (in rna_r1.fastq.gz) and 150bp cdna (in rna_r2.fastq.gz)
# ATAC Modality: 16bp barcode (in atac_r1.fastq.gz) + 150bp gdna (in atac_r2.fastq.gz) + 150bp gdna (in atac_r3.fastq.gz)
$ seqspec init -n myassay -m 2 -o spec.yaml "(((barcode:16,umi:12)rna_r1.fastq.gz,(cdna:150)rna_r2.fastq.gz)rna,((barcode:16)atac_r1.fastq.gz,(gdna:150)atac_r2.fastq.gz,(gdna:150)atac_r3.fastq.gz)atac)"
```

### `seqspec modify`: modify region attributes

```bash
seqspec modify [--region-id REGIONID] [--region-type REGIONTYPE] [--region-name REGIONNAME] [--sequence-type SEQUENCETYPE] [--sequence SEQUENCE] [--min-len MINLEN] [--max-len MAXLEN] -o OUT -r REGIONID -m MODALITY yaml
```

- optionally, `--region-id REGIONID` specifies the new `region_id`.
- optionally, `--region-type REGIONTYPE` specifies the new `region_type`, must come from controlled vocabulary.
- optionally, `--region-name REGIONNAME` specifies the new name for the region.
- optionally, `--sequence-type SEQUENCETYPE` specifies the new sequence type, must come from the controlled vocabulary.
- optionally, `--sequence SEQUENCE` specifies the new sequence for the region.
- optionally, `--min-len MINLEN` sets the new minimum length that the sequence should have.
- optionally, `--max-len MAXLEN` sets the new maximum length that the sequence can have.
- `-o OUT` path to create or overwrite the `seqspec` file.
- `-r REGIONID` is the `region_id` you are specifically targeting for modification.
- `-m MODALITY` is the `modality` containing the `region_id` you are modifying.
- `yaml` corresponds to the `seqspec` file.

_Note_: modifying multiple attributes at one time is currently not supported.

#### Examples

```bash
# rename the atac R1 FASTQ
$ seqspec modify -m rna -o mod.yaml -r "atac_R1_SRR18677642.fastq.gz" --region-id "renamed_atac_R1_SRR18677642.fastq.gz" spec.yaml
```

### `seqspec onlist`: get onlist file for specific regions

```bash
seqspec onlist [-o OUT] -m MODALITY -r REGION yaml
```

- [TODO] optionally, `-o OUT` to set the path of the onlist file.
- `-m MODALITY` is the modality in which you are searching for the region.
- `-r REGION` is the `region_type` for which you want the onlist.
- `yaml` corresponds to the `seqspec` file.

_Note_: If, for example, there are multiple regions with the specified `region_type` in the modality (e.g. multiple barcodes), then `seqspec onlist` will return a path to an onlist that it generates where the entries in that onlist are the cartesian product of the onlists for all of the regions found.

#### Examples

```bash
# get the onlist for the atac barcodes
$ seqspec onlist -m atac -r barcode spec.yaml
/path/to/seqspec/specs/dogmaseq-dig/ATA-737K-arc-v1_rc.txt
```

### `seqspec print`: print seqspec file

```
seqspec print [-o OUT] [-f FORMAT] yaml
```

- optionally, `-o OUT` to set the path of printed file.
- optionally, `-f FORMAT` is the format of the printed file. Can be one of:
  - `tree`: prints an ascii tree of the seqspec
  - `html`: prints html of the seqspec
  - `png`: prints a formal diagram of the seqspec
- `yaml` corresponds to the `seqspec` file.

#### Examples

```
$ seqspec print -f png spec.yaml
```

### `seqspec split`: split seqspec into modalities

```bash
seqspec split -o OUT yaml
```

- optionally, `-o OUT` name prepended to split specs.
- `yaml` corresponds to the `seqspec` file.

#### Examples

```bash
$ seqspec split -o split spec.yaml
$ ls -1
spec.yaml
split.atac.yaml
split.protein.yaml
split.rna.yaml
split.tag.yaml
```

### `seqspec version`: Get seqspec version and seqspec file version

```bash
seqspec version [-o OUT] yaml
```

- optionally, `-o OUT` path to file to write output.
- `yaml` corresponds to the `seqspec` file.

#### Examples

```bash
$ seqspec version spec.yaml
seqspec version: 0.0.0
seqspec file version: 0.0.0
```

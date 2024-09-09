# seqspec

![github version](https://img.shields.io/badge/Version-0.2.0-informational)
[![pypi version](https://img.shields.io/pypi/v/seqspec)](https://pypi.org/project/seqspec/0.2.0/)
![python versions](https://img.shields.io/pypi/pyversions/seqspec)
[![license](https://img.shields.io/pypi/l/seqspec)](LICENSE)

`seqspec` enables uniform processing of genomics data. `seqspec` is a file format and tool that describe data generated from genomics experiments.

A `seqspec` file contains

1. Assay-level metadata such as library kit and sequencing machine,
2. The 5'->3' annotation and position of the elements in a library molecule (e.g. barcodes, UMIs),
3. A list of the reads generated from sequencing the library molecule.

More specifically, `seqspec` is a machine-readable YAML file to describe the content of molecules in genomic libraries, the structure of reads generated from them, and how those are stored in files.

The `seqspec` tool operates on `seqspec` files and

1. Facilitates the standardization of preprocessing steps across different assays,
2. Enables data management and tracking,
3. Simplifies the interpretation and reuse of sequencing data.

<img alt="image" src="/docs/seqspec.png">

```bash
# release
pip install seqspec

# development
pip install git+https://github.com/pachterlab/seqspec.git

# verify install
seqspec --help
```

Documentation:

- [Example `seqspec` files: `https://igvf.github.io/seqspec/`](https://igvf.github.io/seqspec/)
- [Learn about `seqspec` : `docs/DOCUMENTATION.md`](docs/SEQSPEC_FILE.md)
- [Write a `seqspec` : `docs/TUTORIAL.md`](docs/TUTORIAL.md)
- [Contribute a `seqspec` : `docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)
- [The `seqspec` specification : `docs/SPECIFICATION.md`](docs/SPECIFICATION.md)
- [YouTube video that introduces `seqspec`](https://youtu.be/NSj6Vpzy8tU)
- [_bioRxiv_ preprint that describes `seqspec`](https://doi.org/10.1101/2023.03.17.533215)

The `seqspec` format and tool are described in this [publication](https://doi.org/10.1093/bioinformatics/btae168). If you use `seqspec` please cite

```
Ali Sina Booeshaghi, Xi Chen, Lior Pachter, A machine-readable specification for genomics assays, Bioinformatics, Volume 40, Issue 4, April 2024, btae168.
```

`seqspec` was inspired by and builds off of the Teichmann Lab [Single Cell Genomics Library Structure](https://github.com/Teichlab/scg_lib_structs) by [Xi Chen](https://github.com/dbrg77).

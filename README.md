# seqspec

![github version](https://img.shields.io/badge/Version-0.2.0-informational)
[![pypi version](https://img.shields.io/pypi/v/seqspec)](https://pypi.org/project/seqspec/0.2.0/)
![python versions](https://img.shields.io/pypi/pyversions/seqspec)
[![license](https://img.shields.io/pypi/l/seqspec)](LICENSE)

`seqspec` is a file format that describes data generated from genomics experiments. Both the file format and `seqspec` tool [enable uniform processing](./docs/UNIFORM.md) of genomics data.

![alt text](docs/images/simple_file_structure.png)

We have multiple tutorials to get you up and running with `seqspec`:

1. Uniform Preprocessing Tutorial
   Learn how to use `seqspec` to standardize your genomics data preprocessing.
   [View the tutorial](docs/UNIFORM.ipynb)

2. `seqspec` Tool Tutorial
   Discover how to manipulate `seqspec` files using the seqspec command-line tool.
   [View the tutorial](docs/USING_SEQSPEC.ipynb)

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

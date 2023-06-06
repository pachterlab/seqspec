# seqspec

`seqspec` is a machine-readable YAML file format for genomic library sequence and structure. It was inspired by and builds off of the Teichmann Lab [Single Cell Genomics Library Structure](https://github.com/Teichlab/scg_lib_structs) by [Xi Chen](https://github.com/dbrg77).

Genomic library structure depends on the assay used, and read structure depends additionally on the sequencer used to sequence the library. Therefore, a `seqspec` is specific to both a single-cell genomics assay and sequencer. 

A list of `seqspec` examples for multiple assays and sequencers can be found in the `specs/` folder. Each `spec.yaml` describes the 5'->3' "Final library structure" for the assay and sequencer. Sequence specification files can be formatted with the `seqspec` command line tool.

<img alt="image" src="https://github.com/IGVF/seqspec/assets/10369156/c314d7ee-c517-4137-ab48-b10d5ad08304">

```bash
# development
pip install git+https://github.com/IGVF/seqspec.git

# verify install
seqspec --help
```

Documentation:

- [`docs/TUTORIAL.md` : Write a `seqspec`](docs/TUTORIAL.md)
- [`docs/CONTRIBUTING.md` : Contribute a `seqspec`](docs/CONTRIBUTING.md)
- [`docs/SPECIFICATION.md`: The `seqspec` specification](docs/SPECIFICATION.md)
- [YouTube video that introduces `seqspec`](https://youtu.be/NSj6Vpzy8tU)
- [*bioRxiv* preprint that describes `seqspec`](https://doi.org/10.1101/2023.03.17.533215)

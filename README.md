# seqspec

`seqspec` is a machine-readable YAML file format for genomic library sequence and structure. It was inspired by and builds off of the Teichmann Lab [Single Cell Genomics Library Structure](https://github.com/Teichlab/scg_lib_structs) by [Xi Chen](https://github.com/dbrg77).

A list of `seqspec` examples for multiple assays can be found in the `assays/` folder. Each `spec.yaml` describes the 5'->3' "Final library structure" for the assay. Sequence specification files can be formatted with the `seqspec` command line tool.

<img alt="image" src="https://github.com/IGVF/seqspec/assets/10369156/c314d7ee-c517-4137-ab48-b10d5ad08304">

```bash
# development
pip install git+https://github.com/IGVF/seqspec.git

# released
pip install seqspec

seqspec format --help
```

Documentation:

- [`TUTORIAL.md` : Write a `seqspec`](TUTORIAL.md)
- [`CONTRIBUTING.md` : Contribute a `seqspec`](CONTRIBUTING.md)
- [`SPECIFICATION.md`: The `seqspec` specification](SPECIFICATION.md)

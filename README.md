# seqspec

`seqspec` is a machine-readable YAML file format for genomic library sequence and structure. It was inspired by and builds off of the Teichmann Lab [Single Cell Genomics Library Structure](https://github.com/Teichlab/scg_lib_structs) by [Xi Chen](https://github.com/dbrg77).

A list of `seqspec` examples for multiple assays can be found in the `examples/` folder. Each `spec.yaml` describes the 5'->3' "Final library structure" for the assay. Sequence specification files can be formatted with the `seqspec` command line tool.

```bash
pip install git+https://github.com/sbooeshaghi/seqspec.git
seqspec format --help
```

## Specification

Each assay is described by two objects: the `Assay` object and the `Region` object. A library is described by one `Assay` object and multiple (possibly nested) `Region` objects. The `Region` objects are grouped with a `join` operation and an `order` on the sub`Region`s specified. A simple (but not fully specified example) looks like the following:

```
Assay:
    modalities:
        - Modality1
        - Modality2
    assay_spec:
        Modality1:
            join:
                how: Union
                order: [Region2, Region1]
                regions:
                    Region1
                        ...
                    Region2
                        ...
        Modality2:
            ...
```

In order to catalogue relevant information for each library structure, multiple properties are specified for each `Assay` and each `Region`. 

### `Assay` object
`Assay`s have the following structure:

```yaml
# This uses schema based on https://json-schema.org/understanding-json-schema/index.html
$schema: https://json-schema.org/draft/2020-12/schema
$id: Assay.schema.yaml
title: Assay
description: A Assay of DNA
type: object
properties:
  name: 
    description: The name of the assay
    type: string
  doi: 
    description: the doi of the paper that describes the assay
    type: string
  description: 
    description: A short description of the assay
    type: string
  modalities: 
    description: The modalities the assay targets
    type: array
    items:
      type: string
  lib_struct: 
    description: The link to Teichmann's libstructs page derived for this sequence
    type: string
  assay_spec: # should allow for multiple regions, regions should match modalities naming
    description: The spec for the assay
    type: object
    $ref: './Region.schema.yaml'
```

### `Region` object
`Region`s have the following structure:
```yaml
# This uses schema based on https://json-schema.org/understanding-json-schema/index.html
$schema: https://json-schema.org/draft/2020-12/schema
$id: Region.schema.yaml
title: Region
description: A region of DNA
type: object
properties:
  sequence_type:
    description: The type of the sequence
    type: string
  sequence:
    description: The sequence
    type: string
  min_len:
    description: The minimum length of the sequence (left closed)
    type: integer
    minimum: 0
  max_len:
    description: The maximum length of the sequence (right open)
    type: integer
    maximum: 1024
  onlist:
    description: The file containing the sequence if seq_type = onlist
    type: string
  join:
    description: Join operator on regions
    type: object
    properties:
      how:
        description: How the regions will be joined
        type: string
      order: # items in array must match named regions
        description: The order of the regions being joined
        type: array
        items:
          type: string
      regions: # this should technically allow multiple regions
        description: The regions being joined
        type: object
        $ref: '#'
```

## Contributing

Thank you for wanting to improve `seqspec`. If you have a bug that is related to `seqspec` please create an issue. The issue should contain

- the `seqspec` command ran,
- the error message, and
- the `seqspec` and python version.

If you'd like to add assays sequence specifications or make modifications to the `seqspec` tool please do the following:

1. Fork the project.
```
# Press "Fork" at the top right of the GitHub page
```

2. Clone the fork and create a branch for your feature
```bash
git clone https://github.com/<USERNAME>/seqspec.git
cd seqspec
git checkout -b cool-new-feature
```

3. Make changes, add files, and commit
```bash
# make changes, add files, and commit them
git add path/to/file1.yaml path/to/file2.yaml
git commit -m "I made these changes"
```

4. Push changes to GitHub
```bash
git push origin cool-new-feature
```

5. Submit a pull request

If you are unfamilar with pull requests, you can find more information on the [GitHub help page.](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests)

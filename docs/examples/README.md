# Examples

This directory holds the maintained example material for `seqspec`.
It has two parts: canonical examples and a generated HTML site.

## Layout

- `assays/`: maintained assay examples in current `0.4.0` structure
- `reads/`: maintained read templates in current structure
- `regions/`: maintained region templates in current structure
- `site/`: generated static HTML pages built from the maintained examples
- `examples.yaml`: manifest used for validation and site generation

## Status

- `1` `template` assays: intentionally incomplete structure templates
- `51` `example` assays: current examples that load and render but may not fully pass `seqspec check`
- `0` `validated` assays: current examples that pass `seqspec check`

## Regenerate

Run:

```bash
uv run python docs/examples/build_examples.py
```

The script rewrites the maintained YAML, writes the manifest, and regenerates the site.

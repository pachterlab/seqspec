---
title: Installation
date: 2025-08-22
authors:
  - name: A. Sina Booeshaghi
---

# Installation

The development version can be installed with

```bash
# using pip
pip install git+https://github.com/pachterlab/seqspec@devel
# using uv
uv pip install git+https://github.com/pachterlab/seqspec@devel
```

The official release can be installed directly from pypi

```bash
# using pip
pip install seqspec
# using uv
uv pip install seqspec
```

Install from source if you want the current working tree.

```bash
# Python package with the Rust core
uv run maturin develop

# standalone Rust CLI
cargo install --path .
```

Verify the installation.

```bash
seqspec --version
seqspec auth path
```

`seqspec` accepts plain YAML and gzipped YAML (`.yaml.gz`). Remote resources can be configured with `seqspec auth` and used with `--auth-profile` in commands such as `seqspec check` and `seqspec onlist`.

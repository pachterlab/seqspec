# Seqspec Package Documentation

## Introduction

Seqspec is a Python package designed for genomic library sequence and structure specification in a machine-readable format. It provides a set of tools for defining, manipulating, and validating the structure of genomic libraries using YAML files. The package is particularly useful for researchers and bioinformaticians working with genomic data.

## Installation

### Prerequisites

- Python 3.6 or higher
- pip package manager

### Installing Seqspec

Seqspec can be installed using pip. To install the latest release from PyPI, run:

```bash
pip install seqspec
```

To install the development version directly from the GitHub repository, use:

```bash
pip install git+https://github.com/pachterlab/seqspec.git
```

## Usage Guide

Seqspec provides several modules and classes that can be used programmatically or through a command-line interface.

### Programmatic Usage

Here is an example of how to use Seqspec in a Python script:

```python
from seqspec import Assay, Region

# Define a new assay
assay = Assay(name="Example Assay")

# Add regions to the assay
assay.add_region(Region(name="Region 1", sequence="ATCG"))
assay.add_region(Region(name="Region 2", sequence="GGTA"))

# Save the assay specification to a YAML file
assay.to_yaml("example_assay.yaml")
```

### Command-Line Interface (CLI)

Seqspec also provides a CLI for interacting with genomic library specifications. Below are the available subcommands:

- `check`: Validate a seqspec YAML file.
- `find`: Find regions within a seqspec YAML file.
- `format`: Format a seqspec YAML file.
- `index`: Index regions in a seqspec YAML file.
- `info`: Get information about a seqspec YAML file.
- `init`: Initialize a new seqspec YAML file with a given structure.
- `modify`: Modify a seqspec YAML file.
- `onlist`: Retrieve onlist file for regions.
- `print`: Print a seqspec YAML file in various formats.
- `split`: Split a seqspec YAML file into modalities.
- `version`: Get the version of the seqspec tool and YAML file.

Each subcommand comes with a set of options that can be viewed by running `seqspec <subcommand> --help`.

## Tutorials

The following tutorials provide step-by-step instructions for common tasks:

### Creating a New Seqspec File

To create a new seqspec file, you can use the `init` subcommand:

```bash
seqspec init --name "New Assay" --output "new_assay.yaml"
```

This will create a new YAML file with the basic structure for a genomic library assay.

### Validating a Seqspec File

To validate the structure and content of a seqspec file, use the `check` subcommand:

```bash
seqspec check --input "example_assay.yaml"
```

If there are any issues with the file, the `check` command will provide error messages indicating what needs to be fixed.

For more detailed tutorials and examples, please refer to the `TUTORIAL.md` file in the `docs` directory.

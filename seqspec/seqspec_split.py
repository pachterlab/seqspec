"""Split module for seqspec.

This module provides functionality to split seqspec files into one file per modality.
"""
from pathlib import Path
from argparse import ArgumentParser, RawTextHelpFormatter, Namespace
from typing import List

from seqspec.utils import load_spec
from seqspec.Assay import Assay


def setup_split_args(parser) -> ArgumentParser:
    """Create and configure the split command subparser."""
    subparser = parser.add_parser(
        "split",
        description="""
Split seqspec file into one file per modality.

Examples:
seqspec split -o split spec.yaml  # Split spec into modalities
---
""",
        help="Split seqspec file by modality",
        formatter_class=RawTextHelpFormatter,
    )
    subparser_required = subparser.add_argument_group("required arguments")

    subparser.add_argument("yaml", help="Sequencing specification yaml file", type=str)
    subparser_required.add_argument(
        "-o",
        "--output",
        metavar="OUT",
        help="Path to output files",
        type=Path,
        required=True,
    )
    return subparser


def validate_split_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the split command arguments."""
    if not Path(args.yaml).exists():
        parser.error(f"Input file does not exist: {args.yaml}")

    if Path(args.output).exists() and Path(args.output).is_file():
        parser.error(f"Output path exists: {args.output}")


def run_split(parser: ArgumentParser, args: Namespace) -> None:
    """Run the split command."""
    validate_split_args(parser, args)

    spec = load_spec(args.yaml)
    specs = seqspec_split(spec)

    prefix = "spec." if args.output.name == "" else f"{args.output.name}."
    for spec_m in specs:
        modality = spec_m.list_modalities()[0]
        output_path = args.output / f"{prefix}{modality}.yaml"
        spec_m.to_YAML(output_path)


def seqspec_split(spec: Assay) -> List[Assay]:
    """Split spec into one file per modality.

    Args:
        spec: The Assay object to split

    Returns:
        List of Assay objects, each containing a single modality
    """
    specs = []
    modalities = spec.list_modalities()

    # Make a new spec per modality
    for modality in modalities:
        info = {
            "assay_id": spec.assay_id,
            "name": spec.name,
            "doi": spec.doi,
            "date": spec.date,
            "description": spec.description,
            "modalities": [modality],
            "lib_struct": spec.lib_struct,
            "library_kit": spec.library_kit,
            "library_protocol": spec.library_protocol,
            "sequence_kit": spec.sequence_kit,
            "sequence_protocol": spec.sequence_protocol,
            "sequence_spec": spec.get_seqspec(modality),
            "library_spec": [spec.get_libspec(modality)],
            "seqspec_version": spec.seqspec_version,
        }
        spec_m = Assay(**info)
        spec_m.update_spec()
        specs.append(spec_m)

    return specs

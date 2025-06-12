"""Split module for seqspec.

This module provides functionality to split seqspec files into one file per modality.
"""
from pathlib import Path
from argparse import ArgumentParser, RawTextHelpFormatter, Namespace
from typing import List, Dict, Any

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
    specs = split(spec, args.output)

    for spec_info in specs:
        output_path = args.output / f"{spec_info['prefix']}{spec_info['modality']}.yaml"
        spec_info["spec"].to_YAML(output_path)


def split(spec: Assay, output_dir: Path) -> List[Dict[str, Any]]:
    """Split spec into one file per modality."""
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

        prefix = "spec." if output_dir.name == "" else f"{output_dir.name}."
        specs.append({"prefix": prefix, "spec": spec_m, "modality": modality})

    return specs

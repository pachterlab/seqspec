"""Format module for seqspec CLI.

This module provides functionality to automatically format and fill in missing fields
in a seqspec specification file.
"""

from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path

from seqspec.Assay import Assay
from seqspec.utils import load_spec


def setup_format_args(parser) -> ArgumentParser:
    """Create and configure the format command subparser.

    Args:
        parser: The main argument parser to add the format subparser to.

    Returns:
        The configured format subparser.
    """
    subparser = parser.add_parser(
        "format",
        description="""
Automatically fill in missing fields in the spec.

Examples:
seqspec format spec.yaml              # Format spec and write to stdout
seqspec format -o spec.yaml spec.yaml # Format and overwrite the spec
---
""",
        help="Autoformat seqspec file",
        formatter_class=RawTextHelpFormatter,
    )

    subparser.add_argument("yaml", type=Path, help="Sequencing specification yaml file")
    subparser.add_argument(
        "-o",
        "--output",
        metavar="OUT",
        type=Path,
        help="Path to output file",
        default=None,
    )
    return subparser


def validate_format_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the format command arguments.

    Args:
        parser: The argument parser.
        args: The parsed arguments.

    Raises:
        parser.error: If any validation fails.
    """
    if not Path(args.yaml).exists():
        parser.error(f"Input file does not exist: {args.yaml}")

    if args.output and Path(args.output).exists() and not Path(args.output).is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")


def run_format(parser: ArgumentParser, args: Namespace) -> None:
    """Run the format command.

    Args:
        parser: The argument parser.
        args: The parsed arguments.
    """
    validate_format_args(parser, args)

    spec = load_spec(args.yaml, strict=False)
    spec = seqspec_format(spec)

    if args.output:
        spec.to_YAML(args.output)
    else:
        print(spec.to_YAML())


def seqspec_format(spec: Assay) -> Assay:
    """Format a seqspec specification by updating its fields.

    Args:
        spec: The seqspec specification to format.
    """
    spec.update_spec()
    return spec

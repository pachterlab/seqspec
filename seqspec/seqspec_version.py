"""Version module for seqspec.

This module provides functionality to get seqspec tool version and seqspec file version.
"""
from pathlib import Path
from argparse import ArgumentParser, RawTextHelpFormatter, Namespace

from seqspec.utils import load_spec
from seqspec.Assay import Assay
from . import __version__


def setup_version_args(parser) -> ArgumentParser:
    """Create and configure the version command subparser."""
    subparser = parser.add_parser(
        "version",
        description="""
Get seqspec version and seqspec file version.

Examples:
seqspec version -o version.txt spec.yaml  # Save version info to file
seqspec version spec.yaml                 # Print version info to stdout
---
""",
        help="Get seqspec tool version and seqspec file version",
        formatter_class=RawTextHelpFormatter,
    )

    subparser.add_argument("yaml", help="Sequencing specification yaml file", type=Path)
    subparser.add_argument(
        "-o",
        "--output",
        metavar="OUT",
        help="Path to output file",
        type=Path,
        default=None,
    )
    return subparser


def validate_version_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the version command arguments."""
    if not Path(args.yaml).exists():
        parser.error(f"Input file does not exist: {args.yaml}")

    if args.output and Path(args.output).exists() and not Path(args.output).is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")


def run_version(parser: ArgumentParser, args: Namespace) -> None:
    """Run the version command."""
    validate_version_args(parser, args)

    spec = load_spec(args.yaml)
    version_info = version(spec)

    if args.output:
        args.output.write_text(version_info)
    else:
        print(version_info)


def version(spec: Assay) -> str:
    """Get version information for spec and tool."""
    version = spec.seqspec_version
    tool_version = __version__
    return f"seqspec version: {tool_version}\nseqspec file version: {version}"

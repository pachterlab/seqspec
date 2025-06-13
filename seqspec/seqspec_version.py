"""Version module for seqspec.

This module provides functionality to get seqspec tool version and seqspec file version.
"""
from pathlib import Path
from argparse import ArgumentParser, RawTextHelpFormatter, Namespace
from typing import Dict
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
    vinfo = seqspec_version(spec)
    finfo = format_version(vinfo)

    if args.output:
        args.output.write_text(finfo)
    else:
        print(finfo)


def seqspec_version(spec: Assay) -> Dict:
    """Get version information for spec and tool."""
    version = spec.seqspec_version
    tool_version = __version__
    return {"file_version": version, "tool_version": tool_version}


def format_version(vinfo: Dict) -> str:
    """Format version information into a string.

    Args:
        vinfo: Dictionary containing file_version and tool_version

    Returns:
        Formatted string with version information
    """
    return f"seqspec version: {vinfo['tool_version']}\nseqspec file version: {vinfo['file_version']}"

"""Version module for seqspec.

This module provides functionality to get seqspec tool version and seqspec file version.
"""

import os
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path
from typing import Dict

from seqspec.Assay import Assay
from seqspec.utils import is_remote_source, load_spec

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

    subparser.add_argument(
        "yaml", help="Path or URL to sequencing specification YAML", type=str
    )
    subparser.add_argument(
        "-o",
        "--output",
        metavar="OUT",
        help="Path to output file",
        type=Path,
        default=None,
    )
    subparser.add_argument(
        "--auth-profile",
        metavar="PROFILE",
        help="Authentication profile for remote spec access",
        type=str,
        default=os.environ.get("SEQSPEC_AUTH_PROFILE"),
    )
    return subparser


def validate_version_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the version command arguments."""
    if not is_remote_source(args.yaml) and not Path(args.yaml).exists():
        parser.error(f"Input file does not exist: {args.yaml}")

    if args.output and Path(args.output).exists() and not Path(args.output).is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")


def run_version(parser: ArgumentParser, args: Namespace) -> None:
    """Run the version command."""
    validate_version_args(parser, args)

    spec = load_spec(args.yaml, auth_profile=args.auth_profile)
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

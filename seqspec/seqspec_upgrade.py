"""Upgrade module for seqspec.

This module provides functionality to upgrade seqspec files from older versions to the current version.
"""

import os
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path

from seqspec.Assay import Assay
from seqspec.File import File
from seqspec.Region import Onlist
from seqspec.region_type import upgrade_region_type
from seqspec.utils import is_remote_source, load_spec

CURRENT_SEQSPEC_VERSION = "0.5.0"


def setup_upgrade_args(parser) -> ArgumentParser:
    """Create and configure the upgrade command subparser."""
    subparser = parser.add_parser(
        "upgrade",
        description="""
Upgrade seqspec file from older versions to the current version.

Examples:
seqspec upgrade -o upgraded.yaml spec.yaml  # Upgrade and save to new file
seqspec upgrade spec.yaml                   # Upgrade and print to stdout
---
""",
        help="Upgrade seqspec file to current version",
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


def validate_upgrade_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the upgrade command arguments."""
    if not is_remote_source(args.yaml) and not Path(args.yaml).exists():
        parser.error(f"Input file does not exist: {args.yaml}")

    if args.output and Path(args.output).exists() and not Path(args.output).is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")


def run_upgrade(parser: ArgumentParser, args: Namespace) -> None:
    """Run the upgrade command."""
    validate_upgrade_args(parser, args)

    spec = load_spec(args.yaml, strict=False, auth_profile=args.auth_profile)
    version = spec.seqspec_version or "0.0.0"
    upgraded_spec = seqspec_upgrade(spec, version)

    if args.output:
        args.output.write_text(upgraded_spec.to_YAML())
    else:
        print(upgraded_spec.to_YAML())


def seqspec_upgrade(spec: Assay, version: str) -> Assay:
    """Upgrade spec to current version."""
    UPGRADE = {
        "0.0.0": upgrade_0_0_0_to_0_4_0,
        "0.1.0": upgrade_0_1_0_to_0_4_0,
        "0.1.1": upgrade_0_1_1_to_0_4_0,
        "0.2.0": upgrade_0_2_0_to_0_4_0,
        "0.3.0": upgrade_0_3_0_to_0_4_0,
        "0.4.0": upgrade_0_4_0_to_0_4_0,
        "0.5.0": upgrade_0_5_0_to_0_5_0,
    }

    if version not in UPGRADE:
        raise ValueError(
            f"Unsupported version: {version}. Must be one of {list(UPGRADE.keys())}"
        )

    upgraded = UPGRADE[version](spec)
    return upgrade_region_types_to_0_5_0(upgraded)


def upgrade_region_types_to_0_5_0(spec: Assay) -> Assay:
    """Convert region_type values to ontology term lists."""

    def visit(region):
        region.region_type = upgrade_region_type(region.region_type)
        for child in region.regions:
            visit(child)

    for region in spec.library_spec:
        visit(region)
    spec.seqspec_version = CURRENT_SEQSPEC_VERSION
    return spec


def upgrade_0_5_0_to_0_5_0(spec: Assay) -> Assay:
    """Normalize current version specs."""
    return spec


def upgrade_0_4_0_to_0_4_0(spec: Assay) -> Assay:
    """No upgrade needed for current version."""
    return spec


def upgrade_0_3_0_to_0_4_0(spec: Assay) -> Assay:
    """Upgrade spec from version 0.3.0 to 0.4.0."""
    spec.seqspec_version = "0.4.0"
    return spec


def upgrade_0_2_0_to_0_4_0(spec: Assay) -> Assay:
    """Upgrade spec from version 0.2.0 to 0.4.0."""
    # Set files to empty for specs < v0.3.0
    for r in spec.sequence_spec:
        r.set_files(
            [
                File(
                    file_id=r.read_id,
                    filename=r.read_id,
                    filetype="",
                    filesize=0,
                    url="",
                    urltype="",
                    md5="",
                )
            ]
        )

    # Update onlist regions with missing properties
    for r in spec.library_spec:
        for lf in r.get_leaves():
            if lf.onlist is not None:
                filename = lf.onlist.filename
                md5 = lf.onlist.md5
                lf.onlist = Onlist(
                    file_id=filename,
                    filename=filename,
                    filetype="",
                    filesize=0,
                    url="",
                    urltype="",
                    md5=md5,
                )
    spec.seqspec_version = "0.3.0"
    return upgrade_0_3_0_to_0_4_0(spec)


def upgrade_0_1_1_to_0_4_0(spec: Assay) -> Assay:
    """Upgrade spec from version 0.1.1 to 0.4.0."""
    return upgrade_0_2_0_to_0_4_0(spec)


def upgrade_0_1_0_to_0_4_0(spec: Assay) -> Assay:
    """Upgrade spec from version 0.1.0 to 0.4.0."""
    return upgrade_0_2_0_to_0_4_0(spec)


def upgrade_0_0_0_to_0_4_0(spec: Assay) -> Assay:
    """Upgrade spec from version 0.0.0 to 0.4.0."""
    return upgrade_0_2_0_to_0_4_0(spec)

"""Insert module for seqspec CLI.

Provides the standalone ``seqspec insert`` command that can add Regions or
Reads to an existing draft specification.
"""

from __future__ import annotations

import json
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path
from typing import List, Optional

from seqspec.Assay import Assay
from seqspec.Read import Read
from seqspec.Region import Region
from seqspec.utils import load_spec, write_pydantic_to_file_or_stdout

__all__ = ["setup_insert_args", "run_insert"]


# -----------------------------------------------------------------------------
# Arg-parser helpers
# -----------------------------------------------------------------------------


def setup_insert_args(subparsers) -> ArgumentParser:
    sub = subparsers.add_parser(
        "insert",
        help="Insert regions or reads into an existing spec",
        formatter_class=RawTextHelpFormatter,
    )
    req = sub.add_argument_group("required arguments")
    req.add_argument("-m", "--modality", required=True, help="Target modality")
    req.add_argument(
        "-s",
        "--selector",
        required=True,
        choices=["region", "read"],
        help="Section to insert into",
    )
    req.add_argument(
        "-r",
        "--resource",
        required=True,
        metavar="IN",
        help='Path or inline JSON. For reads, expects a list of objects like \'[{"read_id": "R1", "files": ["r1.fastq.gz"]}]\'.',
    )
    sub.add_argument(
        "--after",
        metavar="ID",
        default=None,
        help="Insert after region ID (only for --selector region)",
    )
    sub.add_argument("yaml", type=Path, help="Draft spec to modify")
    sub.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="OUT",
        help="Write updated spec (default stdout)",
    )
    return sub


def validate_insert_args(args: Namespace):
    if args.selector == "region" and args.after == "":
        raise ValueError("Invalid --after value")
    if not Path(args.yaml).exists():
        raise FileNotFoundError(f"Spec file not found: {args.yaml}")


def run_insert(_: ArgumentParser, args: Namespace) -> None:
    validate_insert_args(args)
    spec: Assay = load_spec(args.yaml)

    resource_data = json.loads(args.resource)

    INSERT = {
        "region": lambda x: seqspec_insert_regions(
            spec, args.modality, [Region(**d) for d in resource_data], args.after
        ),
        "read": lambda x: seqspec_insert_reads(
            spec, args.modality, [Read(**d) for d in resource_data], args.after
        ),
    }

    spec = INSERT[args.selector](resource_data)

    spec.update_spec()
    write_pydantic_to_file_or_stdout(spec, args.output)


def seqspec_insert_reads(
    spec: Assay, modality: str, reads: List[Read], after: Optional[str] = None
) -> Assay:
    """Insert regions or reads into the spec."""
    spec.insert_reads(reads, modality, after)

    return spec


def seqspec_insert_regions(
    spec: Assay, modality: str, regions: List[Region], after: Optional[str] = None
) -> Assay:
    """Insert regions or reads into the spec."""
    spec.insert_regions(regions, modality, after)
    return spec

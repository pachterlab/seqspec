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
from seqspec.Read import ReadInput
from seqspec.Region import RegionInput
from seqspec.utils import (
    load_reads,
    load_spec,
    write_pydantic_to_file_or_stdout,
)

__all__ = ["setup_insert_args", "run_insert"]


# -----------------------------------------------------------------------------
# Arg-parser helpers
# -----------------------------------------------------------------------------


def setup_insert_args(subparsers) -> ArgumentParser:
    """Create and configure the ``insert`` subcommand parser.

    Defines required flags to select modality, target section (``read`` or
    ``region``), and the resource payload (path or inline JSON). Also exposes
    optional placement controls and output handling.

    Args:
        subparsers: The subparsers object created by the top-level CLI parser.

    Returns:
        ArgumentParser configured for the ``insert`` subcommand.

    CLI flags:
        - ``-m, --modality``: Target modality (required)
        - ``-s, --selector``: Either ``read`` or ``region`` (required)
        - ``-r, --resource``: Path to YAML/JSON or inline JSON string (required)
        - ``--after``: Insert after a specific region ID (region selector only)
        - positional ``yaml``: Path to draft spec to modify
        - ``-o, --output``: Optional output path; defaults to stdout

    Examples:
        Insert reads from inline JSON:
            seqspec insert -m rna -s read -r '[{"read_id":"R1","files":["r1.fq.gz"]}]' spec.yaml

        Insert regions defined in a file:
            seqspec insert -m rna -s region -r regions.yaml --after rna_primer spec.yaml -o out.yaml
    """
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
    """Validate arguments for the ``insert`` subcommand.

    Ensures the draft spec exists and that ``--after`` is not an empty string
    when used with ``--selector region``.

    Args:
        args: Parsed ``argparse.Namespace`` for the ``insert`` command.

    Raises:
        ValueError: If ``--selector region`` is used with an empty ``--after``.
        FileNotFoundError: If the provided spec ``yaml`` path does not exist.
    """
    if args.selector == "region" and args.after == "":
        raise ValueError("Invalid --after value")
    if not Path(args.yaml).exists():
        raise FileNotFoundError(f"Spec file not found: {args.yaml}")


def run_insert(_: ArgumentParser, args: Namespace) -> None:
    """Execute the ``insert`` command.

    Loads the draft spec, parses the ``--resource`` payload as JSON, and
    dispatches to the appropriate insertion routine based on ``--selector``.
    After insertion, updates derived attributes and writes the result to the
    requested output (file or stdout).

    Args:
        _: The top-level parser (unused here).
        args: Parsed ``argparse.Namespace`` for the ``insert`` command.

    Side effects:
        - Mutates the loaded ``Assay`` in memory.
        - Writes the updated spec to ``--output`` if provided, otherwise prints
          to stdout.
    """
    validate_insert_args(args)
    spec: Assay = load_spec(args.yaml)

    # TODO validate the resource you are loading against the object, i guess this does it already
    resource_data = json.loads(args.resource)
    if args.selector == "reads":
        resource_data = load_reads(resource_data)
        spec = seqspec_insert_reads(spec, args.modality, resource_data, args.after)
    else:
        resource_data = load_reads(resource_data)
        spec = seqspec_insert_reads(spec, args.modality, resource_data, args.after)

    spec.update_spec()
    write_pydantic_to_file_or_stdout(spec, args.output)


def seqspec_insert_reads(
    spec: Assay, modality: str, reads: List[ReadInput], after: Optional[str] = None
) -> Assay:
    """Insert reads into the spec for the given modality.

    Converts each ``ReadInput`` to a ``Read`` and inserts them into the
    ``sequence_spec`` via ``Assay.insert_reads``. If ``after`` is provided, the
    reads are inserted immediately after the read with ID ``after``; otherwise,
    they are inserted at the beginning.

    Args:
        spec: The ``Assay`` to modify. Mutated in place and returned.
        modality: Target modality under which the reads should be inserted.
        reads: A list of ``ReadInput`` objects to insert.
        after: Optional read ID. When provided, insert after this read; when
            ``None``, insert at the start of the reads for the assay.

    Returns:
        The same ``Assay`` instance with reads inserted.

    Example:
        >>> seqspec_insert_reads(spec, "rna", [ReadInput(read_id="R2")], after="R1")
    """
    spec.insert_reads([i.to_read() for i in reads], modality, after)

    return spec


def seqspec_insert_regions(
    spec: Assay, modality: str, regions: List[RegionInput], after: Optional[str] = None
) -> Assay:
    """Insert regions into the library spec for the given modality.

    Converts each ``RegionInput`` to a ``Region`` and inserts them into the
    modality's library via ``Assay.insert_regions``. If ``after`` is provided,
    the regions are inserted immediately after the region with ID ``after``;
    otherwise, they are inserted at the beginning. The library attributes are
    updated by ``Assay.insert_regions``.

    Args:
        spec: The ``Assay`` to modify. Mutated in place and returned.
        modality: Target modality under which the regions should be inserted.
        regions: A list of ``RegionInput`` objects to insert.
        after: Optional region ID. When provided, insert after this region;
            when ``None``, insert at the start of the modality's library.

    Returns:
        The same ``Assay`` instance with regions inserted.

    Example:
        >>> seqspec_insert_regions(spec, "rna", [RegionInput(region_id="new_bc")], after="rna_primer")
    """
    spec.insert_regions([i.to_region() for i in regions], modality, after)
    return spec

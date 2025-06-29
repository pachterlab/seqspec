"""Find module for seqspec CLI.

This module provides functionality to search for objects within seqspec files.
"""

import warnings
from argparse import SUPPRESS, ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path
from typing import List, Optional, Union

from seqspec.Assay import Assay
from seqspec.File import File
from seqspec.Read import Read
from seqspec.Region import Region
from seqspec.seqspec_file import list_all_files
from seqspec.utils import load_spec, write_pydantic_to_file_or_stdout


def setup_find_args(parser) -> ArgumentParser:
    """Create and configure the find command subparser."""
    subparser = parser.add_parser(
        "find",
        description="""
Find objects in the spec.

Examples:
seqspec find -m rna -s read -i rna_R1 spec.yaml         # Find reads by id
seqspec find -m rna -s region-type -i barcode spec.yaml # Find regions with barcode region type
seqspec find -m rna -s file -i r1.fastq.gz spec.yaml    # Find files with id r1.fastq.gz
---
""",
        help="Find objects in seqspec file",
        formatter_class=RawTextHelpFormatter,
    )
    subparser_required = subparser.add_argument_group("required arguments")

    subparser.add_argument("yaml", help="Sequencing specification yaml file", type=Path)
    subparser.add_argument(
        "-o",
        "--output",
        metavar="OUT",
        help="Path to output file",
        type=Path,
        default=None,
    )
    # depracate
    subparser.add_argument("--rtype", help=SUPPRESS, action="store_true")
    choices = ["read", "region", "file", "region-type"]
    subparser.add_argument(
        "-s",
        "--selector",
        metavar="SELECTOR",
        help=f"Selector, [{','.join(choices)}] (default: region)",
        type=str,
        default="region",
        choices=choices,
    )
    subparser_required.add_argument(
        "-m",
        "--modality",
        metavar="MODALITY",
        help="Modality",
        type=str,
        required=True,
    )
    # depracate -r
    subparser_required.add_argument(
        "-r",
        metavar="REGION",
        help=SUPPRESS,
        type=str,
        default=None,
    )
    subparser_required.add_argument(
        "-i",
        "--id",
        metavar="ID",
        help="ID to search for",
        type=str,
        default=None,
        required=False,
    )

    return subparser


def validate_find_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the find command arguments."""
    if not Path(args.yaml).exists():
        parser.error(f"Input file does not exist: {args.yaml}")

    if args.output and Path(args.output).exists() and not Path(args.output).is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")

    if args.r is not None:
        warnings.warn(
            "The '-r' argument is deprecated and will be removed in a future version. "
            "Please use '-i' instead.",
            DeprecationWarning,
        )
        # Optionally map the old option to the new one
        if not args.id:
            args.id = args.r


def seqspec_find(
    spec: Assay, selector: str, modality: str, id: Optional[str] = None
) -> Union[List[Read], List[Region], List[File]]:
    """Core functionality to find objects in a seqspec file.

    Args:
        spec: The Assay object to search in
        selector: Type of object to search for (read, region, file, region-type)
        modality: The modality to search in
        id: The ID to search for (optional)

    Returns:
        List of found objects matching the search criteria:
        - List[Read] for "read" selector
        - List[Region] for "region" and "region-type" selectors
        - List[File] for "file" selector
        - Empty list for unknown selectors
    """

    FIND = {
        "region-type": find_by_region_type,
        "region": find_by_region_id,
        "read": find_by_read_id,
        "file": find_by_file_id,
    }

    if selector not in FIND:
        warnings.warn(
            f"Unknown selector '{selector}'. Valid selectors are: {', '.join(FIND.keys())}"
        )
        return []

    return FIND[selector](spec, modality, id)


def run_find(parser: ArgumentParser, args: Namespace) -> None:
    """Run the find command."""
    validate_find_args(parser, args)

    spec = load_spec(args.yaml)

    found = seqspec_find(spec, args.selector, args.modality, args.id)

    write_pydantic_to_file_or_stdout(found, args.output)


def find_by_read_id(spec: Assay, modality: str, id: Optional[str]) -> List[Read]:
    """Find reads by their ID.

    Args:
        spec: The seqspec specification.
        modality: The modality to search in.
        id: The read ID to search for.

    Returns:
        A list of Read objects matching the ID.
    """
    rds = []
    if id is None:
        return rds
    reads = spec.get_seqspec(modality)
    for r in reads:
        if r.read_id == id:
            rds.append(r)
    return rds


def find_by_file_id(spec: Assay, modality: str, id: Optional[str]) -> List[File]:
    """Find files by their ID.

    Args:
        spec: The seqspec specification.
        modality: The modality to search in.
        id: The file ID to search for.

    Returns:
        A list of File objects matching the ID.
    """
    files = []
    if id is None:
        return files
    lf = list_all_files(spec, modality)
    for k, v in lf.items():
        for f in v:
            if f.file_id == id:
                files.append(f)
    return files


def find_by_region_id(spec: Assay, modality: str, id: Optional[str]) -> List[Region]:
    """Find regions by their ID.

    Args:
        spec: The seqspec specification.
        modality: The modality to search in.
        id: The region ID to search for.

    Returns:
        A list of Region objects matching the ID.
    """
    if id is None:
        return []
    m = spec.get_libspec(modality)
    regions = m.get_region_by_id(id)
    return regions


def find_by_region_type(spec: Assay, modality: str, id: Optional[str]) -> List[Region]:
    """Find regions by their type.

    Args:
        spec: The seqspec specification.
        modality: The modality to search in.
        id: The region type to search for.

    Returns:
        A list of Region objects matching the type.
    """
    if id is None:
        return []
    m = spec.get_libspec(modality)
    regions = m.get_region_by_region_type(id)
    return regions

"""File module for seqspec.

This module provides functionality to list and format files present in seqspec files.
"""

import json
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from seqspec import seqspec_find
from seqspec.Assay import Assay
from seqspec.File import File
from seqspec.utils import load_spec


def setup_file_args(parser) -> ArgumentParser:
    """Create and configure the file command subparser."""
    subparser = parser.add_parser(
        "file",
        description="""
List files present in seqspec file.

Examples:
seqspec file -m rna spec.yaml                                          # List paired read files
seqspec file -m rna -f interleaved spec.yaml                           # List interleaved read files
seqspec file -m rna -f list -k url spec.yaml                           # List urls of all read files
seqspec file -m rna -f list -s region -k all spec.yaml                 # List all files in regions
seqspec file -m rna -f json -s region-type -k all -i barcode spec.yaml # List files for barcode regions in json
---
""",
        help="List files present in seqspec file",
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
    subparser.add_argument(
        "-i",
        "--ids",
        metavar="IDs",
        help="Ids to list",
        type=str,
        default=None,
    )
    subparser_required.add_argument(
        "-m",
        "--modality",
        metavar="MODALITY",
        help="Modality",
        type=str,
        required=True,
    )
    choices = ["read", "region", "file", "region-type"]
    subparser.add_argument(
        "-s",
        "--selector",
        metavar="SELECTOR",
        help=f"Selector for ID, [{', '.join(choices)}] (default: read)",
        type=str,
        default="read",
        choices=choices,
    )
    choices = ["paired", "interleaved", "index", "list", "json"]
    subparser.add_argument(
        "-f",
        "--format",
        metavar="FORMAT",
        help=f"Format, [{', '.join(choices)}], default: paired",
        type=str,
        default="paired",
        choices=choices,
    )
    choices = [
        "file_id",
        "filename",
        "filetype",
        "filesize",
        "url",
        "urltype",
        "md5",
        "all",
    ]
    subparser.add_argument(
        "-k",
        "--key",
        metavar="KEY",
        help=f"Key, [{', '.join(choices)}], default: file_id",
        type=str,
        default="file_id",
        choices=choices,
    )

    # option to get the full path of the file
    subparser.add_argument(
        "--fullpath",
        help="Use full path for local files",
        action="store_true",
        default=False,
    )

    return subparser


def validate_file_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the file command arguments."""
    if not Path(args.yaml).exists():
        parser.error(f"Input file does not exist: {args.yaml}")

    if args.output and Path(args.output).exists() and not Path(args.output).is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")

    if args.key in ["filesize", "filetype", "urltype", "md5"] and args.format in [
        "paired",
        "interleaved",
        "index",
    ]:
        parser.error(
            f"Format '{args.format}' valid only with key 'file_id', 'filename', or 'url'"
        )


def seqspec_file(
    spec: Assay,
    modality: str,
    ids: Optional[List[str]] = None,
    selector: str = "read",
) -> Dict[str, List[File]]:
    """Core functionality to list files from a seqspec.

    Args:
        spec: The Assay object to operate on
        spec_fn: Path to the spec file, used for relative path resolution
        modality: The modality to list files for
        ids: Optional list of IDs to filter by
        selector: Type of ID to filter by (read, region, file, region-type)

    Returns:
        Dictionary mapping IDs to lists of File objects
    """
    # NOTE: LIST FILES DOES NOT RESPECT ORDERING OF INPUT IDs LIST
    # NOTE: seqspec file -s read gets the files for the read, not the files mapped from the regions associated with the read.
    LIST_FILES = {
        "read": list_read_files,
        "region": list_region_files,
        "file": list_all_files,
    }

    LIST_FILES_BY_ID = {
        "read": list_files_by_read_id,
        "file": list_files_by_file_id,
        "region": list_files_by_region_id,
        "region-type": list_files_by_region_type,
    }

    # Get files based on whether we're filtering by IDs
    if not ids:
        # list all files
        return LIST_FILES[selector](spec, modality)
    else:
        # list files by id
        return LIST_FILES_BY_ID[selector](spec, modality, ids)


def run_file(parser: ArgumentParser, args: Namespace) -> None:
    """Run the file command."""
    validate_file_args(parser, args)

    spec = load_spec(args.yaml)
    ids = args.ids.split(",") if args.ids else []

    files = seqspec_file(
        spec=spec,
        modality=args.modality,
        ids=ids,
        selector=args.selector,
    )

    if files:
        FORMAT = {
            "list": format_list_files_metadata,
            "paired": format_list_files,
            "interleaved": format_list_files,
            "index": format_list_files,
            "json": format_json_files,
        }

        result = FORMAT[args.format](
            files, args.format, args.key, Path(args.yaml), args.fullpath
        )

        if args.output:
            args.output.write_text(str(result))
        else:
            print(result)


def list_read_files(spec: Assay, modality: str) -> Dict[str, List[File]]:
    """List files for all reads in a modality."""
    files = defaultdict(list)
    reads = spec.get_seqspec(modality)
    for rd in reads:
        if rd.files:
            files[rd.read_id] = rd.files
    return files


def list_all_files(spec: Assay, modality: str) -> Dict[str, List[File]]:
    """List all files in a modality."""
    files_rd = list_read_files(spec, modality)
    files_rgn = list_region_files(spec, modality)
    return {**files_rd, **files_rgn}


def list_onlist_files(spec, modality):
    files = defaultdict(list)
    regions = spec.get_libspec(modality).get_onlist_regions()
    for r in regions:
        if r.onlist is None:
            continue
        files[r.region_id].append(r.onlist)
    return files


def list_region_files(spec, modality):
    return list_onlist_files(spec, modality)


def format_list_files_metadata(
    files: Dict[str, List[File]],
    fmt: str,
    k: str,
    spec_fn: Path = Path(""),
    fp: bool = False,
) -> str:
    """Format file metadata as a tab-separated list."""
    x = []
    if k == "all":
        for items in zip(*files.values()):
            for key, item in zip(files.keys(), items):
                x.append(
                    f"{key}\t{item.file_id}\t{item.filename}\t{item.filetype}\t{item.filesize}\t{item.url}\t{item.urltype}\t{item.md5}"
                )
    else:
        for items in zip(*files.values()):
            for key, item in zip(files.keys(), items):
                attr = str(getattr(item, k))
                id = item.file_id
                x.append(f"{key}\t{id}\t{attr}")
    return "\n".join(x)


def format_json_files(
    files: Dict[str, List[File]],
    fmt: str,
    k: str,
    spec_fn: Path = Path(""),
    fp: bool = False,
) -> str:
    """Format files as JSON."""
    x = []
    for items in zip(*files.values()):
        if k == "all":
            for key, item in zip(files.keys(), items):
                d = item.to_dict()
                if item.urltype == "local" and fp:
                    d["url"] = str(spec_fn.parent / d["url"])
                x.append(d)
        else:
            for key, item in zip(files.keys(), items):
                attr = getattr(item, k)
                if k == "url" and item.urltype == "local" and fp:
                    attr = str(spec_fn.parent / attr)
                x.append({"file_id": item.file_id, k: attr})
    return json.dumps(x, indent=4)


def format_list_files(
    files: Dict[str, List[File]],
    fmt: str,
    k: Optional[str] = None,
    spec_fn: Path = Path(""),
    fp: bool = False,
) -> str:
    """Format files as a list based on the format type."""
    x = []

    if fmt == "paired":
        for items in zip(*files.values()):
            t = []
            for i in items:
                if k:
                    attr = str(getattr(i, k))
                    if k == "url" and i.urltype == "local" and fp:
                        attr = str(spec_fn.parent / attr)
                    t.append(attr)
                else:
                    t.append(i.filename)
            x.append("\t".join(t))

    elif fmt in ["interleaved", "list"]:
        for items in zip(*files.values()):
            for item in items:
                id = item.filename
                if k:
                    id = str(getattr(item, k))
                    if k == "url" and item.urltype == "local" and fp:
                        id = str(spec_fn.parent / id)
                x.append(id)

    elif fmt == "index":
        t = []
        for items in zip(*files.values()):
            for item in items:
                id = item.filename
                if k:
                    id = str(getattr(item, k))
                    if k == "url" and item.urltype == "local" and fp:
                        id = str(spec_fn.parent / id)
                t.append(id)
        x.append(",".join(t))

    return "\n".join(x)


def list_files_by_read_id(
    spec: Assay, modality: str, read_ids: List[str]
) -> Dict[str, List[File]]:
    """List files for specific read IDs."""
    seqspec = spec.get_seqspec(modality)
    files = defaultdict(list)
    ids = set(read_ids)
    # TODO return the files in the order of the ids given in the input
    # NOTE ORDERING HERE IS IMPORANT SEE GET_INDEX_BY_FILES FUNCTION
    for read in seqspec:
        if read.read_id in ids and read.files:
            files[read.read_id].extend(read.files)
    return files


def list_files_by_file_id(
    spec: Assay, modality: str, file_ids: List[str]
) -> Dict[str, List[File]]:
    """List files for specific file IDs."""
    seqspec = spec.get_seqspec(modality)
    ids = set(file_ids)
    files = defaultdict(list)
    # TODO: NOTE ORDERING HERE IS IMPORTANT SEE RUN_LIST_FILES FUNCTION
    for read in seqspec:
        if read.files:
            for file in read.files:
                if file.filename in ids:
                    files[read.read_id].append(file)
    return files


def list_files_by_region_id(
    spec: Assay, modality: str, region_ids: List[str]
) -> Dict[str, List[File]]:
    """List files for specific region IDs."""
    files = list_region_files(spec, modality)
    ids = set(region_ids)
    new_files = defaultdict(list)
    for region_id, region_files in files.items():
        if region_id in ids:
            new_files[region_id].extend(region_files)
    return new_files


def list_files_by_region_type(
    spec: Assay, modality: str, region_types: List[str]
) -> Dict[str, List[File]]:
    """List files for specific region types."""
    files = list_region_files(spec, modality)
    ids = set(region_types)
    new_files = defaultdict(list)
    for region_id, region_files in files.items():
        r = seqspec_find.find_by_region_id(spec, modality, region_id)[0]
        if r.region_type in ids:
            new_files[region_id].extend(region_files)
    return new_files

"""Onlist module for seqspec CLI.

This module provides functionality to generate and manage onlist files for seqspec regions.
"""

import itertools
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path
from typing import Dict, List

from seqspec.Assay import Assay
from seqspec.Read import Read
from seqspec.Region import Onlist, itx_read, project_regions_to_coordinates
from seqspec.seqspec_find import find_by_region_id, find_by_region_type
from seqspec.utils import (
    load_spec,
    map_read_id_to_regions,
    read_local_list,
    read_remote_list,
)


def setup_onlist_args(parser) -> ArgumentParser:
    """Create and configure the onlist command subparser."""
    subparser = parser.add_parser(
        "onlist",
        description="""
Get onlist file for specific region. Onlist is a list of permissible sequences for a region.

Examples:
seqspec onlist -m rna -s read -i rna_R1 spec.yaml                           # Get onlist URLs for the element in the R1.fastq.gz read
seqspec onlist -m rna -s region-type -i barcode spec.yaml                   # Get onlist URLs for barcode region type
seqspec onlist -m rna -s read -i rna_R1 -o output.txt spec.yaml             # Download and save onlist files
seqspec onlist -m rna -s read -i rna_R1 -f product -o joined.txt spec.yaml  # Join multiple onlists
---
        """,
        help="Get onlist file for elements in seqspec file",
        formatter_class=RawTextHelpFormatter,
    )
    subparser_required = subparser.add_argument_group("required arguments")
    subparser.add_argument("yaml", help="Sequencing specification yaml file", type=Path)

    subparser.add_argument(
        "-o",
        "--output",
        metavar="OUT",
        help="Path to output file (required for download/join operations)",
        type=Path,
        default=None,
    )
    choices = ["read", "region", "region-type"]
    subparser.add_argument(
        "-s",
        "--selector",
        metavar="SELECTOR",
        help=f"Selector for ID, [{', '.join(choices)}] (default: read)",
        type=str,
        default="read",
        choices=choices,
    )

    format_choices = ["product", "multi"]
    subparser.add_argument(
        "-f",
        "--format",
        metavar="FORMAT",
        type=str,
        default=None,
        choices=format_choices,
        help=f"Format for combining multiple onlists ({', '.join(format_choices)})",
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
    subparser_required.add_argument(
        "-m",
        "--modality",
        metavar="MODALITY",
        help="Modality",
        type=str,
        default=None,
        required=True,
    )

    return subparser


def validate_onlist_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the onlist command arguments."""
    if not Path(args.yaml).exists():
        parser.error(f"Input file does not exist: {args.yaml}")

    if args.output and Path(args.output).exists() and not Path(args.output).is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")


def run_onlist(parser: ArgumentParser, args: Namespace) -> None:
    """Run the onlist command."""
    validate_onlist_args(parser, args)

    base_path = args.yaml.parent.absolute()
    spec = load_spec(args.yaml)

    # Get onlists based on selector
    onlists = get_onlists(spec, args.modality, args.selector, args.id)

    if not onlists:
        print("No onlists found")
        return

    # Determine operation based on arguments
    if args.format:
        # Join operation - requires download and output path
        save_path = args.output or Path(args.yaml).resolve().parent
        result_path = join_onlists_and_save(onlists, args.format, save_path, base_path)
        print(result_path)
    elif args.output:
        # Download operation - download remote files to output location
        result_paths = download_onlists_to_path(onlists, args.output, base_path)
        for path_info in result_paths:
            print(f"{path_info['url']}")
    else:
        # List URLs operation - just return the URLs
        urls = get_onlist_urls(onlists, base_path)
        for url_info in urls:
            print(f"{url_info['url']}")


def get_onlists(spec: Assay, modality: str, selector: str, id: str) -> List[Onlist]:
    """Get onlists based on selector type."""
    if selector == "region-type":
        # Prefer ordering by read orientation when possible to ensure
        # consistency with the `read` selector behavior.
        reads: List[Read] = spec.get_seqspec(modality)
        for rd in reads:
            try:
                _, rgns = map_read_id_to_regions(spec, modality, rd.read_id)
            except Exception:
                continue
            ordered_onlists: List[Onlist] = []
            for r in rgns:
                if str(r.region_type) == str(id):
                    ol = r.get_onlist()
                    if ol:
                        ordered_onlists.append(ol)
            if ordered_onlists:
                return ordered_onlists

        # Fallback: original region-type traversal order
        regions = find_by_region_type(spec, modality, id)
        onlists: List[Onlist] = []
        for r in regions:
            ol = r.get_onlist()
            if ol:
                onlists.append(ol)
        return onlists

    elif selector == "region":
        # Use the existing find_by_region_id function
        regions = find_by_region_id(spec, modality, id)
        onlists = []
        for r in regions:
            ol = r.get_onlist()
            if ol:
                onlists.append(ol)
        if not onlists:
            raise ValueError(f"No onlist found for region {id}")
        return onlists

    elif selector == "read":
        # Use existing map_read_id_to_regions function
        (read, rgns) = map_read_id_to_regions(spec, modality, id)
        rcs = project_regions_to_coordinates(rgns)
        new_rcs = itx_read(rcs, 0, read.max_len)

        onlists = []
        for r in new_rcs:
            ol = r.get_onlist()
            if ol:
                onlists.append(ol)
        return onlists

    else:
        raise ValueError(f"Unknown selector: {selector}")


def get_onlist_urls(onlists: List[Onlist], base_path: Path) -> List[Dict[str, str]]:
    """Get URLs for onlists without downloading."""
    urls = []
    for onlist in onlists:
        if onlist.urltype == "local":
            url = str(base_path / Path(onlist.url))
        else:
            url = onlist.url
        urls.append({"file_id": onlist.file_id, "url": url})
    return urls


def download_onlists_to_path(
    onlists: List[Onlist], output_path: Path, base_path: Path
) -> List[Dict[str, str]]:
    """Download remote onlists and return local paths."""
    downloaded_paths = []

    for onlist in onlists:
        if onlist.urltype == "local":
            # Local file - just return the path
            local_path = base_path / Path(onlist.url)
            downloaded_paths.append({"file_id": onlist.file_id, "url": str(local_path)})
        else:
            # Remote file - download it
            onlist_elements = read_remote_list(onlist)
            # Create unique filename for this onlist
            filename = f"{onlist.file_id}_{output_path.name}"
            download_path = output_path.parent / filename
            write_onlist(onlist_elements, download_path)
            downloaded_paths.append(
                {"file_id": onlist.file_id, "url": str(download_path)}
            )

    return downloaded_paths


def join_onlists_and_save(
    onlists: List[Onlist], format_type: str, output_path: Path, base_path: Path
) -> str:
    """Download onlists, join them, and save to output path."""
    # Download all onlists first
    onlist_contents = []
    for onlist in onlists:
        if onlist.urltype == "local":
            content = read_local_list(onlist, str(base_path))
        else:
            content = read_remote_list(onlist)
        onlist_contents.append(content)

    # Join the onlists
    joined_content = join_onlist_contents(onlist_contents, format_type)

    # Save to output path
    write_onlist(joined_content, output_path)
    return str(output_path)


def join_onlist_contents(
    onlist_contents: List[List[str]], format_type: str
) -> List[str]:
    """Join multiple onlist contents using specified format."""
    if format_type == "product":
        return list(join_product_onlist(onlist_contents))
    elif format_type == "multi":
        return list(join_multi_onlist(onlist_contents))
    else:
        raise ValueError(f"Unknown format type: {format_type}")


def write_onlist(onlist: List[str], path: Path) -> None:
    """Write onlist content to file."""
    with open(path, "w") as f:
        for line in onlist:
            f.write(f"{line}\n")


def join_product_onlist(lsts: List[List[str]]):
    """Join onlists using product (cartesian product)."""
    for i in itertools.product(*lsts):
        yield f"{''.join(i)}"


def join_multi_onlist(lsts: List[List[str]]):
    """Join onlists using multi (zip with padding)."""
    for row in itertools.zip_longest(*lsts, fillvalue="-"):
        yield f"{' '.join((str(x) for x in row))}"

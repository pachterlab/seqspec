"""Init module for seqspec CLI.

This module provides functionality to generate new seqspec files from a newick tree format.
"""

import warnings
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path
from typing import List

import newick

from seqspec.Assay import Assay
from seqspec.File import File
from seqspec.Read import Read
from seqspec.Region import Region
from seqspec.utils import write_pydantic_to_file_or_stdout

# example
# seqspec init -n myassay -m 1 -o spec.yaml "(((barcode:16,umi:12)r1.fastq.gz,(cdna:150)r2.fastq.gz)rna)" # seqspec init -n myassay -m 1 -o spec.yaml -r "rna,R1.fastq.gz,truseq_r1,16,pos:rna,R2.fastq.gz,truseq_r2,100,neg" " ((truseq_r1:10,barcode:16,umi:12,cdna:150)rna)"
# seqspec init -n myassay -m 2 -o spec.yaml "(((barcode:16,umi:12)r1.fastq.gz,(cdna:150)r2.fastq.gz)rna,((barcode:16)r1.fastq.gz,(gdna:150)r2.fastq.gz,(gdna:150)r3.fastq.gz)atac)"


def setup_init_args(parser) -> ArgumentParser:
    """Create and configure the init command subparser (simple draft creator)."""
    subparser = parser.add_parser(
        "init",
        description="""
Generate a new *empty* seqspec draft (meta-Regions only).

Example:
    seqspec init -n myassay -m rna,atac -o spec.yaml
""",
        help="Generate a new empty seqspec file",
        formatter_class=RawTextHelpFormatter,
    )
    req = subparser.add_argument_group("required arguments")
    req.add_argument("-n", "--name", required=True, help="Assay name")
    req.add_argument(
        "-m",
        "--modalities",
        required=True,
        help="Comma-separated list of modalities (e.g. rna,atac)",
    )
    subparser.add_argument("--doi", default="", help="DOI of the assay")
    subparser.add_argument("--description", default="", help="Short description")
    subparser.add_argument("--date", default="", help="Date (YYYY-MM-DD)")
    subparser.add_argument(
        "-o", "--output", type=Path, metavar="OUT", help="Output YAML (default stdout)"
    )
    return subparser


def validate_init_args(
    _: ArgumentParser, args: Namespace
) -> None:  # simple draft needs no extra checks
    if not args.name:
        raise ValueError("Assay name is required")
    if not args.modalities:
        raise ValueError("Modalities must be provided")


def run_init(parser: ArgumentParser, args: Namespace) -> None:
    """Run the simplified init command."""
    validate_init_args(parser, args)

    modalities = [m.strip() for m in args.modalities.split(",") if m.strip()]
    spec = seqspec_init(args.name, args.doi, args.date, args.description, modalities)
    # Build empty assay with meta Regions only

    write_pydantic_to_file_or_stdout(spec, args.output)


# -----------------------------------------------------------------------------
# Deprecated legacy (newick-based) helpers – kept for reference only
# -----------------------------------------------------------------------------


warnings.warn(
    "The newick-based seqspec init format is deprecated and will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)


def seqspec_init(
    name: str, doi: str, date: str, description: str, modalities: List[str]
) -> Assay:
    meta_regions: List[Region] = [
        Region(
            region_id=mod, region_type="meta", name=mod, sequence_type="", regions=[]
        )
        for mod in modalities
    ]

    spec = Assay(
        assay_id="",
        name=name,
        doi=doi,
        date=date,
        description=description,
        modalities=modalities,
        lib_struct="",
        sequence_protocol=None,
        sequence_kit=None,
        library_protocol=None,
        library_kit=None,
        sequence_spec=[],
        library_spec=meta_regions,
    )
    spec.update_spec()
    return spec


# The following functions are **deprecated** and unused by the current CLI
# but remain in the file for backward compatibility / reference.


def old_seqspec_init(
    name: str, modalities: List[str], regions: List[Region], reads: List[Read]
) -> Assay:
    """Initialize a new seqspec specification.

    Args:
        name: Name of the assay
        modalities: List of modalities
        regions: List of Region objects
        reads: List of read specifications

    Returns:
        Initialized Assay object

    Raises:
        ValueError: If number of modalities doesn't match number of regions
    """
    if len(regions) != len(modalities):
        raise ValueError("Number of modalities must match number of regions")

    return Assay(
        assay_id="",
        name=name,
        doi="",
        date="",
        description="",
        modalities=modalities,
        lib_struct="",
        library_kit="",
        library_protocol="",
        sequence_kit="",
        sequence_protocol="",
        sequence_spec=reads,
        library_spec=regions,
    )


def newick_to_regions(newick_str: str) -> List[Region]:
    """Convert a newick string to a list of Region objects.

    Args:
        newick_str: Newick format string representing the library structure

    Returns:
        List of Region objects

    Raises:
        ValueError: If newick string is invalid
    """
    try:
        tree = newick.loads(newick_str)
    except Exception as e:
        raise ValueError(f"Invalid newick string: {e}")

    regions = []
    for node in tree[0].descendants:
        region = Region(region_id="", region_type="", name="", sequence_type="")
        regions.append(newick_to_region(node, region))
    return regions


def newick_to_region(node: newick.Node, region: Region) -> Region:
    """Convert a newick node to a Region object.

    Args:
        node: Newick tree node
        region: Base region object to populate

    Returns:
        Populated Region object
    """
    region.region_id = node.name
    region.name = node.name

    if not node.descendants:
        region.min_len = int(node.length)
        region.max_len = int(node.length)
        return region

    region.regions = []
    for descendant in node.descendants:
        region.regions.append(
            newick_to_region(
                descendant,
                Region(
                    region_id=descendant.name,
                    region_type="",
                    name=descendant.name,
                    sequence_type="",
                ),
            )
        )
    return region


def parse_reads_string(input_string: str) -> List[Read]:
    """Parse a string of read specifications into Read objects.

    Args:
        input_string: String containing read specifications in format
            "modality,read_id,primer_id,min_len,strand:..."

    Returns:
        List of Read objects
    """
    reads = []
    for obj in input_string.split(":"):
        modality, read_id, primer_id, min_len, strand = obj.split(",")

        reads.append(
            Read(
                read_id=read_id,
                name=read_id,
                modality=modality,
                primer_id=primer_id,
                min_len=int(min_len),
                max_len=int(min_len),
                strand=strand,
                files=[
                    File(
                        file_id=read_id,
                        filename=read_id,
                        filetype="",
                        filesize=0,
                        url="",
                        urltype="",
                        md5="",
                    )
                ],
            )
        )

    return reads

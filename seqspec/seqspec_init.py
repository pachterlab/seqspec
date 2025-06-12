"""Init module for seqspec CLI.

This module provides functionality to generate new seqspec files from a newick tree format.
"""
from pathlib import Path
from argparse import ArgumentParser, RawTextHelpFormatter, Namespace
from typing import List

import newick
from seqspec.Assay import Assay
from seqspec.Region import Region
from seqspec.File import File
from seqspec.Read import Read

# example
# seqspec init -n myassay -m 1 -o spec.yaml "(((barcode:16,umi:12)r1.fastq.gz,(cdna:150)r2.fastq.gz)rna)" # seqspec init -n myassay -m 1 -o spec.yaml -r "rna,R1.fastq.gz,truseq_r1,16,pos:rna,R2.fastq.gz,truseq_r2,100,neg" " ((truseq_r1:10,barcode:16,umi:12,cdna:150)rna)"
# seqspec init -n myassay -m 2 -o spec.yaml "(((barcode:16,umi:12)r1.fastq.gz,(cdna:150)r2.fastq.gz)rna,((barcode:16)r1.fastq.gz,(gdna:150)r2.fastq.gz,(gdna:150)r3.fastq.gz)atac)"


def setup_init_args(parser) -> ArgumentParser:
    """Create and configure the init command subparser."""
    subparser = parser.add_parser(
        "init",
        description="""
Generate a new seqspec file.

Examples:
seqspec init -o spec.yaml -n myassay -m rna -r rna,R1.fastq.gz,r1_primer,16,pos:rna,R2.fastq.gz,r2_primer,100,neg "((r1_primer:0,barcode:16,umi:12,cdna:150,r2_primer:0)rna)" # Initialize a single modality assay
---
""",
        help="Generate a new seqspec file",
        formatter_class=RawTextHelpFormatter,
    )
    subparser_required = subparser.add_argument_group("required arguments")
    subparser_required.add_argument(
        "-n", "--name", metavar="NAME", type=str, help="Assay name", required=True
    )
    subparser_required.add_argument(
        "-m",
        "--modalities",
        metavar="MODALITIES",
        type=str,
        help="List of comma-separated modalities (e.g. rna,atac)",
        required=True,
    )

    # -r "rna,R1.fastq.gz,truseq_r1,16,pos:rna,R2.fastq.gz,truseq_r2,100,neg"
    subparser_required.add_argument(
        "-r",
        "--reads",
        metavar="READS",
        type=str,
        help="List of modalities, reads, primer_ids, lengths, and strand (e.g. modality,fastq_name,primer_id,len,strand:...)",
        required=True,
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
        "newick",
        help="Tree in newick format (https://marvin.cs.uidaho.edu/Teaching/CS515/newickFormat.html)",
    )
    return subparser


def validate_init_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the init command arguments."""
    if not args.newick:
        parser.error("Newick tree must be provided")

    if args.output and args.output.exists() and not args.output.is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")


def run_init(parser: ArgumentParser, args: Namespace) -> None:
    """Run the init command."""
    validate_init_args(parser, args)

    modalities = args.modalities.split(",")
    reads = parse_reads_string(args.reads)
    tree = newick.loads(args.newick)

    if len(tree[0].descendants) != len(modalities):
        raise ValueError(
            "Number of modalities must match number of modality-FASTQs pairs"
        )

    spec = init(args.name, modalities, tree[0].descendants, reads)

    if args.output:
        spec.to_YAML(args.output)
    else:
        print(spec.to_YAML())


def init(
    name: str, modalities: List[str], tree: List[newick.Node], reads: List[Read]
) -> Assay:
    """Initialize a new seqspec specification.

    Args:
        name: Name of the assay.
        modalities: List of modalities.
        tree: Newick tree nodes.
        reads: List of read specifications.

    Returns:
        Initialized Assay object.
    """
    regions = []
    for node in tree:
        region = Region(region_id="", region_type="", name="", sequence_type="")
        regions.append(newick_to_region(node, region))

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


def newick_to_region(node: newick.Node, region: Region) -> Region:
    """Convert a newick node to a Region object.

    Args:
        node: Newick tree node.
        region: Base region object to populate.

    Returns:
        Populated Region object.
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
        List of Read objects.
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

"""Init module for seqspec CLI.

This module provides functionality to generate new seqspec files from a newick tree format.
"""

from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path
from typing import List

from seqspec.Assay import Assay
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

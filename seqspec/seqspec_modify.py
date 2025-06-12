"""Modify module for seqspec.

This module provides functionality to modify attributes of various elements in seqspec files.
"""
from pathlib import Path
from argparse import ArgumentParser, RawTextHelpFormatter, Namespace, SUPPRESS
from typing import List, Optional
import warnings

from seqspec.utils import load_spec
from seqspec.File import File
from seqspec.Assay import Assay


def setup_modify_args(parser) -> ArgumentParser:
    """Create and configure the modify command subparser."""
    subparser = parser.add_parser(
        "modify",
        description="""
Modify attributes of various elements in a seqspec file.

Examples:
seqspec modify -m rna -o mod_spec.yaml -i rna_R1 --read-id renamed_rna_R1 spec.yaml                                                                                                # modify the read id
seqspec modify -m rna -o mod_spec.yaml -s region -i rna_cell_bc --region-id renamed_rna_cell_bc spec.yaml                                                                        # modify the region id
seqspec modify -m rna -o mod_spec.yaml -i rna_R1 --files "R1_1.fastq.gz,fastq,0,./fastq/R1_1.fastq.gz,local,null:R1_2.fastq.gz,fastq,0,./fastq/R1_2.fastq.gz,local,null" spec.yaml # modify the files for R1 fastq
---
""",
        help="Modify attributes of various elements in seqspec file",
        formatter_class=RawTextHelpFormatter,
    )
    subparser_required = subparser.add_argument_group("required arguments")
    subparser.add_argument("yaml", help="Sequencing specification yaml file", type=str)

    # Read properties
    subparser.add_argument(
        "--read-id",
        metavar="READID",
        help="New ID of read",
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--read-name",
        metavar="READNAME",
        help="New name of read",
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--primer-id",
        metavar="PRIMERID",
        help="New ID of primer",
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--strand",
        metavar="STRAND",
        help="New strand",
        type=str,
        default=None,
    )

    # files to insert into the read
    # format: filename,filetype,filesize,url,urltype,md5:...
    subparser.add_argument(
        "--files",
        metavar="FILES",
        help="New files, (filename,filetype,filesize,url,urltype,md5:...)",
        type=str,
        default=None,
    )

    # Region properties
    subparser.add_argument(
        "--region-id",
        metavar="REGIONID",
        help="New ID of region",
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--region-type",
        metavar="REGIONTYPE",
        help="New type of region",
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--region-name",
        metavar="REGIONNAME",
        help="New name of region",
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--sequence-type",
        metavar="SEQUENCETYPE",
        help="New type of sequence",
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--sequence",
        metavar="SEQUENCE",
        help="New sequence",
        type=str,
        default=None,
    )

    # Read or Region properties
    subparser.add_argument(
        "--min-len",
        metavar="MINLEN",
        help="Min region length",
        type=int,
        default=None,
    )
    subparser.add_argument(
        "--max-len",
        metavar="MAXLEN",
        help="Max region length",
        type=int,
        default=None,
    )

    subparser.add_argument(
        "-o",
        "--output",
        metavar="OUT",
        help="Path to output file",
        type=Path,
        default=None,
    )
    subparser_required.add_argument(
        "-r",
        metavar="READID/REGIONID",
        help=SUPPRESS,
        type=str,
        default=None,
    )
    subparser_required.add_argument(
        "-i",
        metavar="IDs",
        help="IDs",
        type=str,
        default=None,
    )
    choices = ["read", "region"]
    subparser.add_argument(
        "-s",
        "--selector",
        metavar="SELECTOR",
        help=f"Selector for ID, [{', '.join(choices)}] (default: read)",
        type=str,
        default="read",
        choices=choices,
    )
    subparser_required.add_argument(
        "-m",
        "--modality",
        metavar="MODALITY",
        help="Modality of the assay",
        type=str,
        required=True,
    )

    return subparser


def validate_modify_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the modify command arguments."""
    if args.r is not None:
        warnings.warn(
            "The '-r' argument is deprecated and will be removed in a future version. "
            "Please use '-i' instead.",
            DeprecationWarning,
        )
        # Optionally map the old option to the new one
        if not args.i:
            args.i = args.r

    if not Path(args.yaml).exists():
        parser.error(f"Input file does not exist: {args.yaml}")

    if args.output and args.output.exists() and not args.output.is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")


def run_modify(parser: ArgumentParser, args: Namespace) -> None:
    """Run the modify command."""
    validate_modify_args(parser, args)

    spec = load_spec(args.yaml)

    # Read properties
    read_kwd = {
        "read_id": args.read_id,
        "read_name": args.read_name,
        "primer_id": args.primer_id,
        "min_len": args.min_len,
        "max_len": args.max_len,
        "strand": args.strand,
        "files": args.files,
    }

    # Region properties
    region_kwd = {
        "region_id": args.region_id,
        "region_type": args.region_type,
        "name": args.region_name,
        "sequence_type": args.sequence_type,
        "sequence": args.sequence,
        "min_len": args.min_len,
        "max_len": args.max_len,
    }

    if args.selector == "region":
        spec = run_modify_region(spec, args.modality, args.i, **region_kwd)
    elif args.selector == "read":
        spec = run_modify_read(spec, args.modality, args.i, **read_kwd)

    # Update spec
    spec.update_spec()

    if args.output:
        args.output.write_text(spec.to_YAML())
    else:
        print(spec.to_YAML())


def run_modify_read(
    spec: Assay,
    modality: str,
    target_read: str,
    read_id: Optional[str] = None,
    read_name: Optional[str] = None,
    primer_id: Optional[str] = None,
    min_len: Optional[int] = None,
    max_len: Optional[int] = None,
    strand: Optional[str] = None,
    files: Optional[str] = None,
) -> Assay:
    """Modify read properties in spec."""
    reads = spec.get_seqspec(modality)
    if files:
        files_list = parse_files_string(files)
    for r in reads:
        if r.read_id == target_read:
            r.update_read_by_id(
                read_id,
                read_name,
                modality,
                primer_id,
                min_len,
                max_len,
                strand,
                files_list,
            )
    return spec


def run_modify_region(
    spec: Assay,
    modality: str,
    target_region: str,
    region_id: Optional[str] = None,
    region_type: Optional[str] = None,
    name: Optional[str] = None,
    sequence_type: Optional[str] = None,
    sequence: Optional[str] = None,
    min_len: Optional[int] = None,
    max_len: Optional[int] = None,
) -> Assay:
    """Modify region properties in spec."""
    spec.get_libspec(modality).update_region_by_id(
        target_region,
        region_id,
        region_type,
        name,
        sequence_type,
        sequence,
        min_len,
        max_len,
    )
    return spec


def parse_files_string(input_string: str) -> List[File]:
    """Parse files string into list of File objects. # filename,filetype,filesize,url,urltype,md5:..."""
    files = []
    for f in input_string.split(":"):
        filename, filetype, filesize, url, urltype, md5 = f.split(",")
        files.append(
            File(
                file_id=filename,
                filename=filename,
                filetype=filetype,
                filesize=int(filesize),
                url=url,
                urltype=urltype,
                md5=md5,
            )
        )
    return files

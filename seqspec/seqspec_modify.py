"""Modify module for seqspec.

This module provides functionality to modify attributes of various elements in seqspec files.
"""

import json
from argparse import SUPPRESS, ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path
from typing import List

from seqspec.Assay import Assay
from seqspec.utils import load_spec, write_pydantic_to_file_or_stdout


def setup_modify_args(parser) -> ArgumentParser:
    """Create and configure the modify command subparser."""
    subparser = parser.add_parser(
        "modify",
        description="""
Modify attributes of various elements in a seqspec file using JSON objects.

Examples:
seqspec modify -m rna -o mod_spec.yaml -s read -k '[{"read_id": "rna_R1", "name": "renamed_rna_R1"}]' spec.yaml
seqspec modify -m rna -o mod_spec.yaml -s region -k '[{"region_id": "rna_cell_bc", "name": "renamed_rna_cell_bc"}]' spec.yaml
seqspec modify -m rna -o mod_spec.yaml -s file -k '[{"file_id": "R1.fastq.gz", "url": "./fastq/R1.fastq.gz"}]' spec.yaml
seqspec modify -m rna -o mod_spec.yaml -s seqkit -k '[{"kit_id": "NovaSeq_kit", "name": "Updated NovaSeq Kit"}]' spec.yaml
seqspec modify -m rna -o mod_spec.yaml -s seqprotocol -k '[{"protocol_id": "Illumina_NovaSeq", "name": "Updated Protocol"}]' spec.yaml
seqspec modify -m rna -o mod_spec.yaml -s libkit -k '[{"kit_id": "Truseq_kit", "name": "Updated Truseq Kit"}]' spec.yaml
seqspec modify -m rna -o mod_spec.yaml -s libprotocol -k '[{"protocol_id": "10x_protocol", "name": "Updated 10x Protocol"}]' spec.yaml
seqspec modify -m rna -o mod_spec.yaml -s assay -k '[{"assay_id": "my_assay", "name": "Updated Assay Name"}]' spec.yaml
---
""",
        help="Modify attributes of various elements in seqspec file",
        formatter_class=RawTextHelpFormatter,
    )
    subparser_required = subparser.add_argument_group("required arguments")
    subparser.add_argument("yaml", help="Sequencing specification yaml file", type=str)

    subparser_required.add_argument(
        "-k",
        "--keys",
        metavar="KEYS",
        help="JSON array of objects to modify. Each object must include an id field (read_id, region_id, file_id, kit_id, protocol_id, or assay_id).",
        type=str,
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
    # subparser_required.add_argument(
    #     "-r",
    #     metavar="READID/REGIONID",
    #     help=SUPPRESS,
    #     type=str,
    #     default=None,
    # )
    subparser_required.add_argument(
        "-i",
        metavar="IDs",
        help=SUPPRESS,
        type=str,
        default=None,
    )
    choices = [
        "read",
        "region",
        "file",
        "seqkit",
        "seqprotocol",
        "libkit",
        "libprotocol",
        "assay",
    ]
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

    if not Path(args.yaml).exists():
        parser.error(f"Input file does not exist: {args.yaml}")

    if args.output and args.output.exists() and not args.output.is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")


def run_modify(parser: ArgumentParser, args: Namespace) -> None:
    """Run the modify command."""
    validate_modify_args(parser, args)
    # todo enable updating id with args.id
    spec = load_spec(args.yaml)

    keys = json.loads(args.keys)  # list of dicts

    UPDATE = {
        "read": seqspec_modify_read,
        "region": seqspec_modify_region,
        "file": seqspec_modify_files,
        "seqkit": seqspec_modify_seqkit,
        "seqprotocol": seqspec_modify_seqprotocol,
        "libkit": seqspec_modify_libkit,
        "libprotocol": seqspec_modify_libprotocol,
        "assay": seqspec_modify_assay,
    }

    spec = UPDATE.get(args.selector, lambda x: None)[spec, args.modality, keys]

    # Update spec
    spec.update_spec()

    write_pydantic_to_file_or_stdout(spec, args.output)


def seqspec_modify_read(spec: Assay, modality: str, new_reads: List[dict]) -> Assay:
    """Modify read properties in spec using new read objects."""
    reads = spec.get_seqspec(modality)
    for new_read_data in new_reads:
        read_id = new_read_data.get("read_id")
        if not read_id:
            continue
        for read in reads:
            if read.read_id == read_id:
                # Update only the fields that are provided
                for field, value in new_read_data.items():
                    if value is not None and hasattr(read, field):
                        setattr(read, field, value)
                break
    return spec


def seqspec_modify_region(spec: Assay, modality: str, new_regions: List[dict]) -> Assay:
    """Modify region properties in spec using new region objects."""
    libspec = spec.get_libspec(modality)
    for new_region_data in new_regions:
        region_id = new_region_data.get("region_id")
        if not region_id:
            continue
        matching_regions = libspec.get_region_by_id(region_id)
        for region in matching_regions:
            # Update only the fields that are provided
            for field, value in new_region_data.items():
                if value is not None and hasattr(region, field):
                    setattr(region, field, value)
    return spec


def seqspec_modify_files(spec: Assay, modality: str, new_files: List[dict]) -> Assay:
    """Modify file properties in spec using new file objects."""
    reads = spec.get_seqspec(modality)
    for new_file_data in new_files:
        file_id = new_file_data.get("file_id")
        if not file_id:
            continue
        for read in reads:
            for file in read.files:
                if file.file_id == file_id:
                    # Update only the fields that are provided
                    for field, value in new_file_data.items():
                        if value is not None and hasattr(file, field):
                            setattr(file, field, value)
                    break
    return spec


def seqspec_modify_seqkit(spec: Assay, modality: str, new_seqkits: List[dict]) -> Assay:
    """Modify sequence kit properties in spec."""
    if isinstance(spec.sequence_kit, list):
        for new_seqkit_data in new_seqkits:
            kit_id = new_seqkit_data.get("kit_id")
            if not kit_id:
                continue
            for seqkit in spec.sequence_kit:
                if seqkit.kit_id == kit_id:
                    # Update only the fields that are provided
                    for field, value in new_seqkit_data.items():
                        if value is not None and hasattr(seqkit, field):
                            setattr(seqkit, field, value)
                    break
    return spec


def seqspec_modify_seqprotocol(
    spec: Assay, modality: str, new_seqprotocols: List[dict]
) -> Assay:
    """Modify sequence protocol properties in spec."""
    if isinstance(spec.sequence_protocol, list):
        for new_seqprotocol_data in new_seqprotocols:
            protocol_id = new_seqprotocol_data.get("protocol_id")
            if not protocol_id:
                continue
            for seqprotocol in spec.sequence_protocol:
                if seqprotocol.protocol_id == protocol_id:
                    # Update only the fields that are provided
                    for field, value in new_seqprotocol_data.items():
                        if value is not None and hasattr(seqprotocol, field):
                            setattr(seqprotocol, field, value)
                    break
    return spec


def seqspec_modify_libkit(spec: Assay, modality: str, new_libkits: List[dict]) -> Assay:
    """Modify library kit properties in spec."""
    if isinstance(spec.library_kit, list):
        for new_libkit_data in new_libkits:
            kit_id = new_libkit_data.get("kit_id")
            if not kit_id:
                continue
            for libkit in spec.library_kit:
                if libkit.kit_id == kit_id:
                    # Update only the fields that are provided
                    for field, value in new_libkit_data.items():
                        if value is not None and hasattr(libkit, field):
                            setattr(libkit, field, value)
                    break
    return spec


def seqspec_modify_libprotocol(
    spec: Assay, modality: str, new_libprotocols: List[dict]
) -> Assay:
    """Modify library protocol properties in spec."""
    if isinstance(spec.library_protocol, list):
        for new_libprotocol_data in new_libprotocols:
            protocol_id = new_libprotocol_data.get("protocol_id")
            if not protocol_id:
                continue
            for libprotocol in spec.library_protocol:
                if libprotocol.protocol_id == protocol_id:
                    # Update only the fields that are provided
                    for field, value in new_libprotocol_data.items():
                        if value is not None and hasattr(libprotocol, field):
                            setattr(libprotocol, field, value)
                    break
    return spec


def seqspec_modify_assay(
    spec: Assay, modality: str, new_assay_data: List[dict]
) -> Assay:
    """Modify assay properties in spec."""
    for data in new_assay_data:
        assay_id = data.get("assay_id")
        if not assay_id or assay_id != spec.assay_id:
            continue
        # Update only the fields that are provided
        for field, value in data.items():
            if value is not None and hasattr(spec, field):
                setattr(spec, field, value)
    return spec

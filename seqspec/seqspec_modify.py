"""Modify module for seqspec.

This module provides functionality to modify attributes of various elements in seqspec files.
"""

import json
from argparse import SUPPRESS, ArgumentParser, Namespace, RawTextHelpFormatter
from enum import Enum
from pathlib import Path
from typing import List

from seqspec.Assay import (
    Assay,
    AssayInput,
    LibKitInput,
    LibProtocolInput,
    SeqKitInput,
    SeqProtocolInput,
)
from seqspec.File import FileInput
from seqspec.Read import ReadInput
from seqspec.Region import RegionInput
from seqspec.utils import (
    load_assays,
    load_files,
    load_libkits,
    load_libprotocols,
    load_reads,
    load_regions,
    load_seqkits,
    load_seqprotocols,
    load_spec,
    write_pydantic_to_file_or_stdout,
)


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

    # TODO make this a potential path to a yaml file or json file
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

    # Parse inline JSON string into a list of dicts; sub-functions will load objects
    raw_keys = json.loads(args.keys)
    if not isinstance(raw_keys, list):
        parser.error("--keys must be a JSON array of objects")

    keys = raw_keys

    spec = seqspec_modify(spec, args.modality, keys, args.selector)

    # Update spec
    spec.update_spec()

    write_pydantic_to_file_or_stdout(spec, args.output)


class Selector(str, Enum):
    READ = "read"
    REGION = "region"
    FILE = "file"
    SEQKIT = "seqkit"
    SEQPROTOCOL = "seqprotocol"
    LIBKIT = "libkit"
    LIBPROTOCOL = "libprotocol"
    ASSAY = "assay"


def seqspec_modify(
    spec: Assay,
    modality: str,
    keys: list[dict],
    selector: Selector,
) -> Assay:
    """Modify a loaded spec in-place according to selector-specific updates.

    This is the core implementation behind the ``seqspec modify`` CLI.
    It dispatches to a section-specific updater based on ``selector`` and
    applies partial updates to items identified by their stable IDs. Only
    fields present in each input object and not ``None`` are applied.

    Args:
        spec: Parsed ``Assay`` object to modify. Mutated in place and returned.
        modality: Target modality within the spec (for example, "rna", "atac").
        keys: List of JSON-like dictionaries describing updates. Each dict must
            include the identifying field for the chosen ``selector``:
            - selector == "read": use "read_id"
            - selector == "region": use "region_id"
            - selector == "file": use "file_id"
            - selector == "seqkit": use "kit_id"
            - selector == "seqprotocol": use "protocol_id"
            - selector == "libkit": use "kit_id"
            - selector == "libprotocol": use "protocol_id"
            - selector == "assay": use "assay_id" (must match ``spec.assay_id``)
        selector: Section of the spec to modify. See ``Selector`` enum.

    Returns:
        The same ``Assay`` instance with updates applied.

    Notes:
        - Read updates support the optional "files" field; when provided, the
          inputs are converted to ``File`` models before assignment.
        - Region updates are applied via ``Region.update_region_by_id`` within
          the library spec of the given modality.
        - Sequence/Library kits and protocols are updated field-by-field when
          the item with the matching ID is found; unknown IDs are ignored.
        - Unknown or missing identifiers in ``keys`` are skipped without error.

    Examples:
        Update a read name:
            >>> seqspec_modify(spec, "rna", [{"read_id": "rna_R1", "name": "R1_renamed"}], "read")

        Update a region sequence:
            >>> seqspec_modify(spec, "rna", [{"region_id": "rna_cell_bc", "sequence": "NNNN"}], "region")

        Update an assay description:
            >>> seqspec_modify(spec, "rna", [{"assay_id": spec.assay_id, "description": "New desc"}], "assay")
    """
    LOADERS = {
        Selector.READ: load_reads,
        Selector.REGION: load_regions,
        Selector.FILE: load_files,
        Selector.SEQKIT: load_seqkits,
        Selector.SEQPROTOCOL: load_seqprotocols,
        Selector.LIBKIT: load_libkits,
        Selector.LIBPROTOCOL: load_libprotocols,
        Selector.ASSAY: load_assays,
    }
    UPDATERS = {
        Selector.READ: seqspec_modify_read,
        Selector.REGION: seqspec_modify_region,
        Selector.FILE: seqspec_modify_files,
        Selector.SEQKIT: seqspec_modify_seqkit,
        Selector.SEQPROTOCOL: seqspec_modify_seqprotocol,
        Selector.LIBKIT: seqspec_modify_libkit,
        Selector.LIBPROTOCOL: seqspec_modify_libprotocol,
        Selector.ASSAY: seqspec_modify_assay,
    }

    selector_enum = selector if isinstance(selector, Selector) else Selector(selector)
    loader = LOADERS.get(selector_enum)
    updater = UPDATERS.get(selector_enum)
    if loader is None or updater is None:
        return spec

    loaded_inputs = loader(keys)
    mod_spec: Assay = updater(spec, modality, loaded_inputs)  # type: ignore[arg-type]
    return mod_spec


def seqspec_modify_read(
    spec: Assay, modality: str, new_reads: List[ReadInput]
) -> Assay:
    """Modify read properties in spec using ``ReadInput`` objects."""
    reads = spec.get_seqspec(modality)
    for patch in new_reads:
        read_id = getattr(patch, "read_id", None)
        if not read_id:
            continue
        for read in reads:
            if read.read_id == read_id:
                files_value = None
                if "files" in patch.model_fields_set and patch.files is not None:
                    files_value = [f.to_file() for f in patch.files]
                read.update_read_by_id(
                    read_id=patch.read_id,
                    name=patch.name,
                    modality=patch.modality,
                    primer_id=patch.primer_id,
                    min_len=patch.min_len,
                    max_len=patch.max_len,
                    strand=patch.strand,
                    files=files_value,
                )
                break
    return spec


def seqspec_modify_region(
    spec: Assay, modality: str, new_regions: List[RegionInput]
) -> Assay:
    """Modify region properties in spec using ``RegionInput`` objects."""
    libspec = spec.get_libspec(modality)
    for patch in new_regions:
        region_id = getattr(patch, "region_id", None)
        if not region_id:
            continue
        libspec.update_region_by_id(
            target_region_id=region_id,
            region_id=patch.region_id,
            region_type=patch.region_type,
            name=patch.name,
            sequence_type=patch.sequence_type,
            sequence=patch.sequence,
            min_len=patch.min_len,
            max_len=patch.max_len,
        )
    return spec.model_copy()


def seqspec_modify_files(
    spec: Assay, modality: str, new_files: List[FileInput]
) -> Assay:
    """Modify file properties in spec using ``FileInput`` objects."""
    reads = spec.get_seqspec(modality)
    for patch in new_files:
        file_id = getattr(patch, "file_id", None)
        if not file_id:
            continue
        for read in reads:
            for file in read.files:
                if file.file_id == file_id:
                    for field in patch.model_fields_set:
                        value = getattr(patch, field)
                        if value is not None:
                            setattr(file, field, value)
                    break
    return spec


def seqspec_modify_seqkit(
    spec: Assay, modality: str, new_seqkits: List[SeqKitInput]
) -> Assay:
    """Modify sequence kit properties in spec using ``SeqKitInput`` objects."""
    if isinstance(spec.sequence_kit, list):
        for patch in new_seqkits:
            kit_id = getattr(patch, "kit_id", None)
            if not kit_id:
                continue
            for seqkit in spec.sequence_kit:
                if seqkit.kit_id == kit_id:
                    for field in patch.model_fields_set:
                        value = getattr(patch, field)
                        if value is not None and hasattr(seqkit, field):
                            setattr(seqkit, field, value)
                    break
    return spec


def seqspec_modify_seqprotocol(
    spec: Assay,
    modality: str,
    new_seqprotocols: List[SeqProtocolInput],
) -> Assay:
    """Modify sequence protocol properties using ``SeqProtocolInput`` objects."""
    if isinstance(spec.sequence_protocol, list):
        for patch in new_seqprotocols:
            protocol_id = getattr(patch, "protocol_id", None)
            if not protocol_id:
                continue
            for seqprotocol in spec.sequence_protocol:
                if seqprotocol.protocol_id == protocol_id:
                    for field in patch.model_fields_set:
                        value = getattr(patch, field)
                        if value is not None and hasattr(seqprotocol, field):
                            setattr(seqprotocol, field, value)
                    break
    return spec


def seqspec_modify_libkit(
    spec: Assay, modality: str, new_libkits: List[LibKitInput]
) -> Assay:
    """Modify library kit properties in spec using ``LibKitInput`` objects."""
    if isinstance(spec.library_kit, list):
        for patch in new_libkits:
            kit_id = getattr(patch, "kit_id", None)
            if not kit_id:
                continue
            for libkit in spec.library_kit:
                if libkit.kit_id == kit_id:
                    for field in patch.model_fields_set:
                        value = getattr(patch, field)
                        if value is not None and hasattr(libkit, field):
                            setattr(libkit, field, value)
                    break
    return spec


def seqspec_modify_libprotocol(
    spec: Assay,
    modality: str,
    new_libprotocols: List[LibProtocolInput],
) -> Assay:
    """Modify library protocol properties using ``LibProtocolInput`` objects."""
    if isinstance(spec.library_protocol, list):
        for patch in new_libprotocols:
            protocol_id = getattr(patch, "protocol_id", None)
            if not protocol_id:
                continue
            for libprotocol in spec.library_protocol:
                if libprotocol.protocol_id == protocol_id:
                    for field in patch.model_fields_set:
                        value = getattr(patch, field)
                        if value is not None and hasattr(libprotocol, field):
                            setattr(libprotocol, field, value)
                    break
    return spec


def seqspec_modify_assay(
    spec: Assay, modality: str, new_assay_data: List[AssayInput]
) -> Assay:
    """Modify assay properties using ``AssayInput`` objects."""
    for patch in new_assay_data:
        assay_id = getattr(patch, "assay_id", None)
        if not assay_id or assay_id != spec.assay_id:
            continue
        for field in patch.model_fields_set:
            value = getattr(patch, field)
            if value is not None and hasattr(spec, field):
                setattr(spec, field, value)
    return spec

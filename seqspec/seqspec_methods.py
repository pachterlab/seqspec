"""Methods module for seqspec.

This module provides functionality to convert seqspec files into methods sections.
"""
from pathlib import Path
from argparse import ArgumentParser, RawTextHelpFormatter, Namespace

from seqspec.utils import load_spec
from seqspec.Assay import Assay
from seqspec.Region import Region
from seqspec.Read import Read, File


def setup_methods_args(parser) -> ArgumentParser:
    """Create and configure the methods command subparser."""
    subparser = parser.add_parser(
        "methods",
        description="""
Convert seqspec file into methods section.

Examples:
seqspec methods -m rna -o methods.txt spec.yaml  # Save methods section to file
seqspec methods -m rna spec.yaml                 # Print methods section to stdout
---
""",
        help="Convert seqspec file into methods section",
        formatter_class=RawTextHelpFormatter,
    )
    subparser_required = subparser.add_argument_group("required arguments")

    subparser.add_argument("yaml", help="Sequencing specification yaml file", type=str)
    subparser_required.add_argument(
        "-m",
        "--modality",
        metavar="MODALITY",
        help="Modality",
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
    return subparser


def validate_methods_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the methods command arguments."""
    if not Path(args.yaml).exists():
        parser.error(f"Input file does not exist: {args.yaml}")

    if args.output and args.output.exists() and not args.output.is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")


def run_methods(parser: ArgumentParser, args: Namespace) -> None:
    """Run the methods command."""
    validate_methods_args(parser, args)

    spec = load_spec(args.yaml)
    methods_text = methods(spec, args.modality)

    if args.output:
        args.output.write_text(methods_text)
    else:
        print(methods_text)


def methods(spec: Assay, modality: str) -> str:
    """Generate methods section for spec and modality."""
    m = f"""Methods
The {modality} portion of the {spec.name} assay was generated on {spec.date}.
    """
    m += format_library_spec(spec, modality)
    return m


# TODO: manage sequence/library protocol/kit for cases where each modality has different protocols/kits
def format_library_spec(spec: Assay, modality: str) -> str:
    """Format library specification for methods section."""
    leaves = spec.get_libspec(modality).get_leaves()

    lib_prot = None
    if isinstance(spec.library_protocol, str):
        lib_prot = spec.library_protocol
    elif isinstance(spec.library_protocol, list):
        for i in spec.library_protocol:
            if i.modality == modality:
                lib_prot = i.protocol_id

    lib_kit = None
    if isinstance(spec.library_kit, str):
        lib_kit = spec.library_kit
    elif isinstance(spec.library_kit, list):
        for i in spec.library_kit:
            if i.modality == modality:
                lib_kit = i.kit_id

    seq_prot = None
    if isinstance(spec.sequence_protocol, str):
        seq_prot = spec.sequence_protocol
    elif isinstance(spec.sequence_protocol, list):
        for i in spec.sequence_protocol:
            if i.modality == modality:
                seq_prot = i.protocol_id

    seq_kit = None
    if isinstance(spec.sequence_kit, str):
        seq_kit = spec.sequence_kit
    elif isinstance(spec.sequence_kit, list):
        for i in spec.sequence_kit:
            if i.modality == modality:
                seq_kit = i.kit_id

    s = f"""
Libary structure\n
The library was generated using the {lib_prot} library protocol and {lib_kit} library kit. The library contains the following elements:\n
"""
    for idx, r in enumerate(leaves, 1):
        s += format_region(r, idx)
    s += f"""
\nSequence structure\n
The library was sequenced on a {seq_prot} using the {seq_kit} sequencing kit. The library was sequenced using the following configuration:\n
"""
    reads = spec.get_seqspec(modality)
    for idx, r in enumerate(reads, 1):
        s += format_read(r, idx)
    return s


def format_region(region: Region, idx: int = 1) -> str:
    """Format region for methods section."""
    s = f"{idx}. {region.name}: {region.min_len}-{region.max_len}bp {region.sequence_type} sequence ({region.sequence})"
    if region.onlist:
        s += f", onlist file: {region.onlist.filename}.\n"
    else:
        s += ".\n"
    return s


def format_read(read: Read, idx: int = 1) -> str:
    """Format read for methods section."""
    s = f"- {read.name}: {read.max_len} cycles on the {'positive' if read.strand == 'pos' else 'negative'} strand using the {read.primer_id} primer. The following files contain the sequences in Read {idx}:\n"
    if read.files:
        for idx, f in enumerate(read.files, 1):
            s += "  " + format_read_file(f, idx)
    return s


def format_read_file(file: File, idx: int = 1) -> str:
    """Format read file for methods section."""
    return f"- File {idx}: {file.filename}\n"

from seqspec.utils import load_spec
import json
from typing import List
from seqspec.Region import Region
from seqspec.Read import Read
from seqspec.Assay import Assay
from argparse import RawTextHelpFormatter, ArgumentParser, Namespace
from pathlib import Path


def setup_info_args(parser) -> ArgumentParser:
    """Create and configure the info command subparser."""
    subparser = parser.add_parser(
        "info",
        description="""
Get information about spec.

Examples:
seqspec info -k modalities spec.yaml            # Get the list of modalities
seqspec info -f json spec.yaml                  # Get meta information in json format
seqspec info -f json -k library_spec spec.yaml  # Get library spec in json format
seqspec info -f json -k sequence_spec spec.yaml # Get sequence spec in json format
---
""",
        help="Get information from seqspec file",
        formatter_class=RawTextHelpFormatter,
    )

    subparser.add_argument("yaml", help="Sequencing specification yaml file", type=Path)
    choices = ["modalities", "meta", "sequence_spec", "library_spec"]
    subparser.add_argument(
        "-k",
        "--key",
        metavar="KEY",
        help=f"Object to display, [{', '.join(choices)}] (default: meta)",
        type=str,
        default="meta",
        required=False,
    )
    choices = ["tab", "json"]
    subparser.add_argument(
        "-f",
        "--format",
        metavar="FORMAT",
        help=f"The output format, [{', '.join(choices)}] (default: tab)",
        type=str,
        default="tab",
        required=False,
        choices=choices,
    )
    subparser.add_argument(
        "-o",
        "--output",
        metavar="OUT",
        help="Path to output file",
        type=Path,
        default=None,
        required=False,
    )
    return subparser


def validate_info_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the info command arguments."""
    if not Path(args.yaml).exists():
        parser.error(f"Input file does not exist: {args.yaml}")

    if args.output and Path(args.output).exists() and not Path(args.output).is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")


def run_info(parser: ArgumentParser, args: Namespace) -> None:
    """Run the info command."""
    validate_info_args(parser, args)

    spec = load_spec(args.yaml)
    CMD = {
        "modalities": seqspec_info_modalities,
        "meta": seqspec_info,
        "sequence_spec": seqspec_info_sequence_spec,
        "library_spec": seqspec_info_library_spec,
    }
    s = ""
    if args.key:
        s = CMD[args.key](spec, args.format)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(s, f, sort_keys=False, indent=4)
    else:
        print(s)


def seqspec_info(spec: Assay, fmt: str) -> str:
    """Get meta information about the spec."""
    s = format_info(spec, fmt)
    return s


def seqspec_info_library_spec(spec: Assay, fmt: str) -> str:
    """Get library specification information."""
    modalities = spec.list_modalities()
    s = ""
    for m in modalities:
        libspec = spec.get_libspec(m)
        s += format_library_spec(m, libspec.get_leaves(), fmt)
    return s


def seqspec_info_sequence_spec(spec: Assay, fmt: str) -> str:
    """Get sequence specification information."""
    reads = format_sequence_spec(spec.sequence_spec, fmt)
    return reads


def seqspec_info_modalities(spec: Assay, fmt: str) -> str:
    """Get list of modalities."""
    modalities = format_modalities(spec.list_modalities(), fmt)
    return modalities


def format_info(spec: Assay, fmt: str = "tab") -> str:
    """Format meta information."""
    sd = spec.to_dict()
    del sd["library_spec"]
    del sd["sequence_spec"]
    del sd["modalities"]
    s = ""
    if fmt == "tab":
        for k, v in sd.items():
            s += f"{v}\t"
        s = s[:-1]
    elif fmt == "json":
        s = json.dumps(sd, sort_keys=False, indent=4)
    return s


def format_modalities(modalities: List[str], fmt: str = "tab") -> str:
    """Format list of modalities."""
    s = ""
    if fmt == "tab":
        s = "\t".join(modalities)
    elif fmt == "json":
        s = json.dumps(modalities, sort_keys=False, indent=4)
    return s


def format_sequence_spec(sequence_spec: List[Read], fmt: str = "tab") -> str:
    """Format sequence specification."""
    s = ""
    if fmt == "tab":
        # format the output as a table
        for r in sequence_spec:
            files = ",".join([i.file_id for i in r.files]) if r.files else ""
            s += f"{r.modality}\t{r.read_id}\t{r.strand}\t{r.min_len}\t{r.max_len}\t{r.primer_id}\t{r.name}\t{files}\n"
        s = s[:-1]
    elif fmt == "json":
        s = json.dumps([i.to_dict() for i in sequence_spec], sort_keys=False, indent=4)
    return s


def format_library_spec(
    modality: str, library_spec: List[Region], fmt: str = "tab"
) -> str:
    """Format library specification."""
    s = ""
    if fmt == "tab":
        for r in library_spec:
            file = None
            if r.onlist:
                file = r.onlist.filename
            s += f"{modality}\t{r.region_id}\t{r.region_type}\t{r.name}\t{r.sequence_type}\t{r.sequence}\t{r.min_len}\t{r.max_len}\t{file}\n"
        s = s[:-1]
    elif fmt == "json":
        s = json.dumps(
            {modality: [i.to_dict() for i in library_spec]}, sort_keys=False, indent=4
        )
    return s

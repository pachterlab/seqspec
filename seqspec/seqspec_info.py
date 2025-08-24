import json
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path
from typing import Dict

from seqspec.Assay import Assay
from seqspec.utils import load_spec


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

    if args.key:
        # Extract data
        info = seqspec_info(spec, args.key)
        # Format info
        result = format_info(info, args.key, args.format)

        if args.output:
            with open(args.output, "w") as f:
                if args.format == "json":
                    f.write(result)
                else:
                    print(result, file=f)
        else:
            print(result)


def seqspec_info(spec: Assay, key: str) -> Dict:
    """Get information from the spec based on the key.

    Args:
        spec: The Assay object to get info from
        key: The type of information to retrieve (modalities, meta, sequence_spec, library_spec)

    Returns:
        Dictionary containing the requested information

    Raises:
        KeyError: If the requested key is not supported
    """
    INFO_FUNCS = {
        "modalities": seqspec_info_modalities,
        "meta": seqspec_info_meta,
        "sequence_spec": seqspec_info_sequence_spec,
        "library_spec": seqspec_info_library_spec,
    }
    if key not in INFO_FUNCS:
        raise KeyError(
            f"Unsupported info key: {key}. Must be one of {list(INFO_FUNCS.keys())}"
        )
    return INFO_FUNCS[key](spec)


def format_info(info: Dict, key: str, fmt: str = "tab") -> str:
    """Format information based on the key and format.

    Args:
        info: Dictionary containing the information to format
        key: The type of information to format (modalities, meta, sequence_spec, library_spec)
        fmt: Output format (tab or json)

    Returns:
        Formatted string

    Raises:
        KeyError: If the requested key is not supported
    """
    FORMAT_FUNCS = {
        "modalities": format_modalities,
        "meta": format_meta,
        "sequence_spec": format_sequence_spec,
        "library_spec": format_library_spec,
    }
    if key not in FORMAT_FUNCS:
        raise KeyError(
            f"Unsupported format key: {key}. Must be one of {list(FORMAT_FUNCS.keys())}"
        )
    return FORMAT_FUNCS[key](info, fmt)


def seqspec_info_meta(spec: Assay) -> Dict:
    """Get meta information about the spec.

    Args:
        spec: The Assay object to get info from

    Returns:
        Dictionary containing meta information
    """
    sd = spec.to_dict()
    del sd["library_spec"]
    del sd["sequence_spec"]
    del sd["modalities"]
    return {"meta": sd}


def seqspec_info_library_spec(spec: Assay) -> Dict:
    """Get library specification information.

    Args:
        spec: The Assay object to get info from

    Returns:
        Dictionary containing library specifications by modality
    """
    modalities = spec.list_modalities()
    result = {}
    for m in modalities:
        libspec = spec.get_libspec(m)
        leaves = libspec.get_leaves()
        result[m] = leaves if leaves else []
    return {"library_spec": result}


def seqspec_info_sequence_spec(spec: Assay) -> Dict:
    """Get sequence specification information.

    Args:
        spec: The Assay object to get info from

    Returns:
        Dictionary containing sequence specifications
    """
    return {"sequence_spec": [i.model_dump() for i in spec.sequence_spec]}


def seqspec_info_modalities(spec: Assay) -> Dict:
    """Get list of modalities.

    Args:
        spec: The Assay object to get info from

    Returns:
        Dictionary containing list of modalities
    """
    return {"modalities": spec.list_modalities()}


def format_meta(info: Dict, fmt: str = "tab") -> str:
    """Format meta information.

    Args:
        info: Dictionary containing meta information from seqspec_info_meta
        fmt: Output format (tab or json)

    Returns:
        Formatted string
    """
    if fmt == "tab":
        return "\t".join(str(v) for v in info["meta"].values())
    elif fmt == "json":
        return json.dumps(info["meta"], sort_keys=False, indent=4)
    return ""


def format_modalities(info: Dict, fmt: str = "tab") -> str:
    """Format list of modalities.

    Args:
        info: Dictionary containing modalities from seqspec_info_modalities
        fmt: Output format (tab or json)

    Returns:
        Formatted string
    """
    if fmt == "tab":
        return "\t".join(info["modalities"])
    elif fmt == "json":
        return json.dumps(info["modalities"], sort_keys=False, indent=4)
    return ""


def format_sequence_spec(info: Dict, fmt: str = "tab") -> str:
    """Format sequence specification.

    Args:
        info: Dictionary containing sequence specs from seqspec_info_sequence_spec
        fmt: Output format (tab or json)

    Returns:
        Formatted string
    """
    if fmt == "tab":
        lines = []
        for r in info["sequence_spec"]:
            files = ",".join([i["file_id"] for i in r["files"]]) if r["files"] else ""
            lines.append(
                f"{r['modality']}\t{r['read_id']}\t{r['strand']}\t{r['min_len']}\t{r['max_len']}\t{r['primer_id']}\t{r['name']}\t{files}"
            )
        return "\n".join(lines)
    elif fmt == "json":
        return json.dumps(
            [i.model_dump() for i in info["sequence_spec"]], sort_keys=False, indent=4
        )
    return ""


def format_library_spec(info: Dict, fmt: str = "tab") -> str:
    """Format library specification.

    Args:
        info: Dictionary containing library specs from seqspec_info_library_spec
        fmt: Output format (tab or json)

    Returns:
        Formatted string
    """
    if fmt == "tab":
        lines = []
        for modality, regions in info["library_spec"].items():
            for r in regions:
                file = r["onlist"]["filename"] if r["onlist"] else None
                lines.append(
                    f"{modality}\t{r['region_id']}\t{r['region_type']}\t{r['name']}\t{r['sequence_type']}\t{r['sequence']}\t{r['min_len']}\t{r['max_len']}\t{file}"
                )
        return "\n".join(lines)
    elif fmt == "json":
        return json.dumps(
            {m: [i.model_dump() for i in r] for m, r in info["library_spec"].items()},
            sort_keys=False,
            indent=4,
        )
    return ""

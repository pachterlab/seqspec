from seqspec.utils import load_spec
import json
from typing import List
from seqspec.Region import Region
from seqspec.Read import Read
from seqspec.Assay import Assay
from argparse import RawTextHelpFormatter


def setup_info_args(parser):
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

    subparser.add_argument("yaml", help="Sequencing specification yaml file")
    choices = ["modalities", "meta", "sequence_spec", "library_spec"]
    subparser.add_argument(
        "-k",
        metavar="KEY",
        help=(f"Object to display, [{', '.join(choices)}] (default: meta)"),
        type=str,
        default="meta",
        required=False,
    )
    choices = ["tab", "json"]
    subparser.add_argument(
        "-f",
        metavar="FORMAT",
        help=(f"The output format, [{', '.join(choices)}] (default: tab)"),
        type=str,
        default="tab",
        required=False,
        choices=choices,
    )
    subparser.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
        required=False,
    )
    return subparser


def validate_info_args(parser, args):
    spec_fn = args.yaml
    o = args.o
    k = args.k
    fmt = args.f
    return run_info(spec_fn, fmt, k, o)


def run_info(spec_fn, f, k=None, o=None):
    # return json of the Assay object
    spec = load_spec(spec_fn)
    CMD = {
        "modalities": seqspec_info_modalities,
        "meta": seqspec_info,
        "sequence_spec": seqspec_info_sequence_spec,
        "library_spec": seqspec_info_library_spec,
    }
    s = ""
    if k:
        s = CMD[k](spec, f)

    if o:
        with open(o, "w") as f:
            json.dump(s, f, sort_keys=False, indent=4)
    else:
        print(s)
    return


def seqspec_info(spec, fmt):
    s = format_info(spec, fmt)
    return s


def seqspec_info_library_spec(spec, fmt):
    modalities = spec.list_modalities()
    s = ""
    for m in modalities:
        libspec = spec.get_libspec(m)
        s += format_library_spec(m, libspec.get_leaves(), fmt)
    return s


def seqspec_info_sequence_spec(spec: Assay, fmt):
    reads = format_sequence_spec(spec.sequence_spec, fmt)
    return reads


def seqspec_info_modalities(spec, fmt):
    modalities = format_modalities(spec.list_modalities(), fmt)
    return modalities


def format_info(spec: Assay, fmt="tab"):
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


def format_modalities(modalities: List[str], fmt="tab"):
    s = ""
    if fmt == "tab":
        s = "\t".join(modalities)
    elif fmt == "json":
        s = json.dumps(modalities, sort_keys=False, indent=4)
    return s


def format_sequence_spec(sequence_spec: List[Read], fmt="tab"):
    s = ""
    if fmt == "tab":
        # format the output as a table
        for r in sequence_spec:
            s += f"{r.modality}\t{r.read_id}\t{r.strand}\t{r.min_len}\t{r.max_len}\t{r.primer_id}\t{r.name}\t{','.join([i.file_id for i in r.files])}\n"
        s = s[:-1]
    elif fmt == "json":
        s = json.dumps([i.to_dict() for i in sequence_spec], sort_keys=False, indent=4)
    return s


def format_library_spec(modality: str, library_spec: List[Region], fmt="tab"):
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

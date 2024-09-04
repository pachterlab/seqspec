from seqspec.utils import load_spec
from seqspec.Assay import Assay
from seqspec.Region import Region


def setup_methods_args(parser):
    subparser = parser.add_parser(
        "methods",
        description="Return methods section of sequencing specification",
        help="Return methods section of sequencing specification",
    )
    subparser_required = subparser.add_argument_group("required arguments")

    subparser.add_argument("yaml", help="Sequencing specification yaml file")
    subparser_required.add_argument(
        "-m",
        metavar="MODALITY",
        help=("Modality"),
        type=str,
        default=None,
        required=True,
    )
    subparser.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
    )
    return subparser


def validate_methods_args(parser, args):
    # if everything is valid the run_methods
    fn = args.yaml
    o = args.o

    m = args.m
    return run_methods(fn, m, o)


def run_methods(spec_fn, m, o):
    spec = load_spec(spec_fn)
    m = methods(spec, m)

    if o:
        with open(o, "w") as f:
            print(m, file=f)
    else:
        print(m)


def methods(spec, modality):
    m = f"""Methods
The {modality} portion of the {spec.name} assay was generated on {spec.date}.
    """
    m += format_library_spec(spec, modality)
    return m


# TODO: manage sequence/library protocol/kit for cases where each modality has different protocols/kits
def format_library_spec(spec: Assay, m):
    leaves = spec.get_libspec(m).get_leaves()
    s = f"""
Libary structure\n
The library was generated using the {spec.library_protocol} library protocol and {spec.library_kit} library kit. The library contains the following elements:\n
"""
    for idx, r in enumerate(leaves, 1):
        s += format_region(r, idx)
    s += f"""
\nRead structure\n
The library was sequenced on a {spec.sequence_protocol} using the {spec.sequence_kit} sequencing kit. The library was sequenced using the following configuration:\n
"""
    reads = spec.get_seqspec(m)
    for idx, r in enumerate(reads, 1):
        s += format_read(r, idx)
    return s


def format_region(region: Region, idx: int = 1):
    s = f"{idx}. {region.name}: {region.min_len}-{region.max_len}bp {region.sequence_type} sequence ({region.sequence})"
    if region.onlist:
        s += f", onlist file: {region.onlist.filename}.\n"
    else:
        s += ".\n"
    return s


def format_read(read, idx: int = 1):
    s = f"- {read.name}: {read.max_len} cycles on the {'positive' if read.strand == 'pos' else 'negative'} strand using the {read.primer_id} primer.\n"
    return s

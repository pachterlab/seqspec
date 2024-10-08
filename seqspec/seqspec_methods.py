from seqspec.utils import load_spec
from seqspec.Assay import Assay
from seqspec.Region import Region
from argparse import RawTextHelpFormatter


def setup_methods_args(parser):
    subparser = parser.add_parser(
        "methods",
        description="""
Convert seqspec file into methods section.

Examples:
seqspec methods -m rna spec.yaml # Return methods section for rna modality
---
""",
        help="Convert seqspec file into methods section",
        formatter_class=RawTextHelpFormatter,
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

    lib_prot = None
    if isinstance(spec.library_protocol, str):
        lib_prot = spec.library_protocol
    elif isinstance(spec.library_protocol, list):
        for i in spec.library_protocol:
            if i.modality == m:
                lib_prot = i.protocol_id

    lib_kit = None
    if isinstance(spec.library_kit, str):
        lib_kit = spec.library_kit
    elif isinstance(spec.library_kit, list):
        for i in spec.library_kit:
            if i.modality == m:
                lib_kit = i.kit_id

    seq_prot = None
    if isinstance(spec.sequence_protocol, str):
        seq_prot = spec.sequence_protocol
    elif isinstance(spec.sequence_protocol, list):
        for i in spec.sequence_protocol:
            if i.modality == m:
                seq_prot = i.protocol_id

    seq_kit = None
    if isinstance(spec.sequence_kit, str):
        seq_kit = spec.sequence_kit
    elif isinstance(spec.sequence_kit, list):
        for i in spec.sequence_kit:
            if i.modality == m:
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
    s = f"- {read.name}: {read.max_len} cycles on the {'positive' if read.strand == 'pos' else 'negative'} strand using the {read.primer_id} primer. The following files contain the sequences in Read {idx}:\n"
    for idx, f in enumerate(read.files, 1):
        s += "  " + format_read_file(f, idx)
    s = s[:-1]
    return s


def format_read_file(file, idx: int = 1):
    s = f"- File {idx}: {file.filename}\n"
    return s

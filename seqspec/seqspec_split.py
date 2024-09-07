import os
from seqspec.utils import load_spec
from seqspec.Assay import Assay
from argparse import RawTextHelpFormatter


def setup_split_args(parser):
    subparser = parser.add_parser(
        "split",
        description="""
Split seqspec file into one file per modality.

Examples:
seqspec split -o split spec.yaml # Split spec into modalities
---
""",
        help="split seqspec into modalities",
        formatter_class=RawTextHelpFormatter,
    )
    subparser_required = subparser.add_argument_group("required arguments")

    subparser.add_argument("yaml", help="Sequencing specification yaml file")
    subparser_required.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
        required=True,
    )
    return subparser


def validate_split_args(parser, args):
    # if everything is valid the run_split
    fn = args.yaml
    o = args.o
    return run_split(fn, o)


def run_split(spec_fn, o):
    spec = load_spec(spec_fn)
    specs = split(spec, o)

    for spec in specs:
        spec["spec"].to_YAML(
            os.path.join(os.path.dirname(o), f"{spec['p']}{spec['m']}.yaml")
        )
    return


def split(spec, o=""):
    specs = []
    modalities = spec.list_modalities()
    # make a new spec per modality
    for m in modalities:
        info = {
            "assay_id": spec.assay_id,
            "name": spec.name,
            "doi": spec.doi,
            "date": spec.date,
            "description": spec.description,
            "modalities": [m],
            "lib_struct": spec.lib_struct,
            "library_kit": spec.library_kit,
            "library_protocol": spec.library_protocol,
            "sequence_kit": spec.sequence_kit,
            "sequence_protocol": spec.sequence_protocol,
            "sequence_spec": spec.get_seqspec(m),
            "library_spec": [spec.get_libspec(m)],
            "seqspec_version": spec.seqspec_version,
        }
        spec_m = Assay(**info)
        spec_m.update_spec()
        base_o = "spec." if os.path.basename(o) == "" else f"{os.path.basename(o)}."
        specs.append({"p": base_o, "spec": spec_m, "m": m})
    return specs

import os
from seqspec.utils import load_spec
from seqspec.Assay import Assay


def setup_split_args(parser):
    subparser = parser.add_parser(
        "split",
        description="split seqspec file into modalities",
        help="split seqspec into modalities",
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
    spec = load_spec(fn)
    modalities = spec.list_modalities()
    # make a new spec per modality
    for m in modalities:
        spec_m = Assay(
            spec.assay,
            spec.sequencer,
            spec.name,
            spec.doi,
            spec.publication_date,
            spec.description,
            [m],
            spec.lib_struct,
            [spec.get_modality(m)],
            spec.seqspec_version,
        )
        spec_m.update_spec()
        base_o = "spec." if os.path.basename(o) == "" else f"{os.path.basename(o)}."

        spec_m.to_YAML(os.path.join(os.path.dirname(o), f"{base_o}{m}.yaml"))


def run_split(spec):
    pass

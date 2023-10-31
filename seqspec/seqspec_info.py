from seqspec.utils import load_spec
import json


def setup_info_args(parser):
    subparser = parser.add_parser(
        "info",
        description="get info about seqspec file",
        help="get info about seqspec file",
    )

    subparser.add_argument("yaml", help="Sequencing specification yaml file")
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
    # if everything is valid the run_info
    fn = args.yaml
    o = args.o
    spec = load_spec(fn)
    info = run_info(spec)

    if o:
        with open(o, "w") as f:
            json.dump(info, f, sort_keys=False, indent=4)
    else:
        print(json.dumps(info, sort_keys=False, indent=4))


def run_info(spec):
    # return json of the Assay object
    info = spec.to_dict()
    del info["assay_spec"]
    return info

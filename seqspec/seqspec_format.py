from seqspec.utils import load_spec


def setup_format_args(parser):
    subparser = parser.add_parser(
        "format",
        description="format seqspec file",
        help="format seqspec file",
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


def validate_format_args(parser, args):
    # if everything is valid the run_format
    fn = args.yaml
    o = args.o
    spec = load_spec(fn)
    run_format(spec)
    spec.to_YAML(o)


def run_format(spec):
    spec.update_spec()

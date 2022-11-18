from seqspec.utils import load_spec


def setup_format_args(parser):
    parser_format = parser.add_parser(
        "format",
        description="format seqspec file",
        help="format seqspec file",
    )
    parser_format.add_argument("yaml", help="Sequencing specification yaml file")
    parser_format.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
    )
    return parser_format


def validate_format_args(parser, args):
    # if everything is valid the run_format
    fn = args.yaml
    o = args.o
    spec = load_spec(fn)
    run_format(spec)
    spec.to_YAML(o)


def run_format(spec):
    spec.update_spec()

from seqspec.Assay import Assay
import yaml


def setup_format_args(parser):
    parser_format = parser.add_parser(
        "format",
        description="Format seqspec file",
        help="Format seqspec file",
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
    run_format(fn, o)


def run_format(fn, o):
    with open(fn, "r") as stream:
        data: Assay = yaml.load(stream, Loader=yaml.Loader)
    data.update_spec()
    data.to_YAML(o)

from seqspec.utils import load_spec
from argparse import RawTextHelpFormatter


def setup_format_args(parser):
    subparser = parser.add_parser(
        "format",
        description="""
Automatically fill in missing fields in the spec.

Examples:
seqspec format spec.yaml # Format spec
---
""",
        help="format seqspec file",
        formatter_class=RawTextHelpFormatter,
    )
    # subparser_required = subparser.add_argument_group("required arguments")

    subparser.add_argument("yaml", help="Sequencing specification yaml file")
    subparser.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
    )
    return subparser


def validate_format_args(parser, args):
    fn = args.yaml
    o = args.o

    run_format(spec_fn=fn, o=o)


def run_format(spec_fn, o):
    spec = load_spec(spec_fn)
    format(spec)
    if o:
        spec.to_YAML(o)
    else:
        print(spec.to_YAML())


def format(spec):
    return spec.update_spec()

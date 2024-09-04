from seqspec.utils import load_spec
from . import __version__


def setup_version_args(parser):
    subparser = parser.add_parser(
        "version",
        description="Get seqspec version and seqspec file version",
        help="Get seqspec version and seqspec file version",
    )

    subparser.add_argument("yaml", help="Sequencing specification yaml file")
    subparser.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
    )
    return subparser


def validate_version_args(parser, args):
    # if everything is valid the run_version
    fn = args.yaml
    o = args.o
    run_version(fn, o)


def run_version(spec_fn, o):
    spec = load_spec(spec_fn)
    s = version(spec)
    if o:
        with open(o, "w") as f:
            print(s, file=f)
    else:
        print(s)
    return


def version(spec):
    version = spec.seqspec_version
    tool_version = __version__
    s = f"seqspec version: {tool_version}\nseqspec file version: {version}"
    return s

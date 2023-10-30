from .Region import Region
from seqspec.Assay import Assay
from seqspec.utils import load_spec


def setup_diff_args(parser):
    parser_diff = parser.add_parser(
        "diff",
        description="diff two seqspecs",
        help="diff two seqspecs",
    )
    parser_diff.add_argument("yamlA", help="Sequencing specification yaml file A")
    parser_diff.add_argument("yamlB", help="Sequencing specification yaml file B")
    parser_diff.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
    )
    return parser_diff


def validate_diff_args(parser, args):
    # if everything is valid the run_diff
    A_fn = args.yamlA
    B_fn = args.yamlB
    # o = args.o
    A = load_spec(A_fn)
    B = load_spec(B_fn)

    # load in two specs
    run_diff(A, B)


def run_diff(A: Assay, B: Assay):
    # What does it mean to diff two assays?
    # Only compare on modalities?
    # itx: pull out regions that have the same name?
    # itx:
    pass


def diff_regions(R1: Region, R2: Region):
    pass

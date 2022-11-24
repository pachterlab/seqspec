from seqspec.utils import load_spec, get_cuts
from seqspec.seqspec_find import run_find


def setup_index_args(parser):
    parser_index = parser.add_parser(
        "index",
        description="index regions in a seqspec file",
        help="index regions in a seqspec file",
    )
    parser_index.add_argument("yaml", help="Sequencing specification yaml file")
    parser_index.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
    )
    parser_index.add_argument(
        "-m",
        metavar="MODALITY",
        help=("Modality"),
        type=str,
        default=None,
    )
    parser_index.add_argument(
        "-r",
        metavar="REGION",
        help=("Region"),
        type=str,
        default=None,
    )
    parser_index.add_argument(
        "--rev", help="Returns 3'->5' region order", action="store_true"
    )
    return parser_index


def validate_index_args(parser, args):
    # if everything is valid the run_index
    # get paramters
    fn = args.yaml
    m = args.m
    r = args.r
    o = args.o
    rev = args.rev

    # load spec
    spec = load_spec(fn)

    cuts, rtypes = run_index(spec, m, r, rev)

    # post processing
    if o:
        with open(o, "w") as f:
            for c, rt in zip(cuts, rtypes):
                print(f"{rt}\t{c[0]}\t{c[1]}", file=f)
    else:
        for c, rt in zip(cuts, rtypes):
            print(f"{rt}\t{c[0]}\t{c[1]}")


def run_index(spec, modality, region, rev=False):
    # run function
    regions = run_find(spec, modality, region)
    leaves = regions[0].get_leaves()
    if rev:
        leaves.reverse()
    cuts = get_cuts(leaves)
    rtypes = [i.region_type for i in leaves]
    return (cuts, rtypes)

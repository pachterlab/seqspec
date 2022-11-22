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

    # run function
    regions = run_find(spec, m, r)
    leaves = regions[0].get_leaves()
    if rev:
        leaves.reverse()
    cuts = get_cuts(leaves)

    # post processing
    if o:
        with open(o, "w") as f:
            for c, l in zip(cuts, leaves):
                print(f"{l.region_id}\t{c[0]}\t{c[1]}", file=f)
    else:
        for c, l in zip(cuts, leaves):
            print(f"{l.region_id}\t{c[0]}\t{c[1]}")

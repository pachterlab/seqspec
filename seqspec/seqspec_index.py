from seqspec.utils import load_spec, get_cuts
from seqspec.seqspec_find import run_find
from collections import defaultdict
from typing import Dict, List, Tuple


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

    index = run_index(spec, m, r, rev=rev)

    # post processing
    if o:
        with open(o, "w") as f:
            for k, v in index.items():
                print(f"{v}\t{k[0]}\t{k[1]}", file=f)
    else:
        for k, v in index.items():
            print(f"{v}\t{k[0]}\t{k[1]}")


def run_index_by_type(
    spec, modality, region_id, rev=False
) -> Dict[str, List[Tuple[int, int]]]:
    rid = region_id
    # run function
    index = defaultdict(list)
    regions = run_find(spec, modality, rid)
    leaves = regions[0].get_leaves()
    if rev:
        leaves.reverse()
    cuts = get_cuts(leaves)

    # groupby requested region
    for idx, l in enumerate(leaves):
        t = l.region_type
        c = cuts[idx]

        index[t].extend([c])
    return index


def run_index(spec, modality, region_id, rev=False) -> Dict[Tuple[int, int], str]:
    rid = region_id
    # run function
    index = defaultdict()
    regions = run_find(spec, modality, rid)
    leaves = regions[0].get_leaves()
    if rev:
        leaves.reverse()
    cuts = get_cuts(leaves)

    for idx, l in enumerate(leaves):
        t = l.region_type
        c = cuts[idx]
        index[c] = t

    return index

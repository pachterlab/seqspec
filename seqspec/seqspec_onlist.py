from seqspec.Assay import Assay
from seqspec.utils import load_spec
from seqspec.seqspec_find import run_find_by_type
import os
from seqspec.utils import read_list
import itertools


def setup_onlist_args(parser):
    subparser = parser.add_parser(
        "onlist",
        description="get onlist file for specific region",
        help="get onlist file for specific regions",
    )
    subparser_required = subparser.add_argument_group("required arguments")
    subparser.add_argument("yaml", help="Sequencing specification yaml file")
    subparser.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
    )
    subparser_required.add_argument(
        "-m",
        metavar="MODALITY",
        help=("Modality"),
        type=str,
        default=None,
        required=True,
    )
    subparser_required.add_argument(
        "-r", metavar="REGION", help=("Region"), type=str, default=None, required=True
    )
    return subparser


def validate_onlist_args(parser, args):
    # get paramters
    fn = args.yaml
    m = args.m
    r = args.r
    # TODO: if onlist is a link, download. also fix output path
    # o = args.o
    # load spec
    spec = load_spec(fn)
    # if number of barcodes > 1 then we need to join them

    olist = run_onlist(spec, m, r)
    print(os.path.join(os.path.dirname(os.path.abspath(fn)), olist))
    return


def run_onlist(spec: Assay, modality: str, region_id: str):
    # for now return the path to the onlist file for the modality/region pair

    # run function
    regions = run_find_by_type(spec, modality, region_id)
    onlists = []
    for r in regions:
        onlists.append(r.get_onlist().filename)

    return join_onlists(onlists)


def join_onlists(onlists):
    base_path = os.path.dirname(os.path.abspath(onlists[0]))
    if len(onlists) == 1:
        return onlists[0]
    else:
        # join the onlists
        lsts = [read_list(o) for o in onlists]
        joined_path = os.path.join(base_path, "onlist_joined.txt")
        with open(joined_path, "w") as f:
            for i in itertools.product(*lsts):
                f.write(f"{''.join(i)}\n")
        return joined_path

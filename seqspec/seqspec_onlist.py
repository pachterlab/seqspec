from seqspec.Assay import Assay
from seqspec.utils import load_spec
from seqspec.seqspec_find import run_find
import os


def setup_onlist_args(parser):
    subparser = parser.add_parser(
        "onlist",
        description="get onlist file for specific region",
        help="get onlist file for specific regions",
    )
    subparser.add_argument("yaml", help="Sequencing specification yaml file")
    subparser.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "-m",
        metavar="MODALITY",
        help=("Modality"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "-r",
        metavar="REGION",
        help=("Region"),
        type=str,
        default=None,
    )
    # subparser.add_argument(
    #     "-j",
    #     metavar="JOIN",
    #     help=("Join"),
    #     type=str,
    #     default=None,
    # )
    return subparser


def validate_onlist_args(parser, args):
    # get paramters
    fn = args.yaml
    m = args.m
    r = args.r
    o = args.o
    # load spec
    spec = load_spec(fn)
    olist = run_onlist(spec, m, r)
    print(os.path.join(os.path.dirname(os.path.abspath(fn)), olist))
    return


def run_onlist(spec: Assay, modality: str, region_id: str):
    # for now return the path to the onlist file for the modality/region pair

    # run function
    regions = run_find(spec, modality, region_id)
    olist = regions[0].get_onlist().filename

    return olist

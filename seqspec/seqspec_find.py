from seqspec.utils import load_spec
from seqspec.Assay import Assay
import yaml


def setup_find_args(parser):
    parser_find = parser.add_parser(
        "find",
        description="find regions in a seqspec file",
        help="find regions in a seqspec file",
    )
    parser_find.add_argument("yaml", help="Sequencing specification yaml file")
    parser_find.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
    )
    parser_find.add_argument(
        "-m",
        metavar="MODALITY",
        help=("Modality"),
        type=str,
        default=None,
    )
    parser_find.add_argument(
        "-r",
        metavar="REGION",
        help=("Region"),
        type=str,
        default=None,
    )
    return parser_find


def validate_find_args(parser, args):
    # if everything is valid the run_find
    # get paramters
    fn = args.yaml
    m = args.m
    r = args.r
    o = args.o

    # load spec
    spec = load_spec(fn)

    # run function
    regions = run_find(spec, m, r)

    # post processing
    if o:
        with open(o, "w") as f:
            yaml.dump(regions, f, sort_keys=False)
    else:
        print(yaml.dump(regions, sort_keys=False))


def run_find(spec: Assay, modality: str, region_id: str):
    m = spec.get_modality(modality)
    regions = m.get_region_by_id(region_id)
    return regions

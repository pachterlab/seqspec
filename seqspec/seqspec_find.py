from seqspec.utils import load_spec
from seqspec.Assay import Assay
import yaml


def setup_find_args(parser):
    subparser = parser.add_parser(
        "find",
        description="find regions in a seqspec file",
        help="find regions in a seqspec file",
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
    subparser.add_argument("--rtype", help="Find by region type", action="store_true")
    subparser_required.add_argument(
        "-m",
        metavar="MODALITY",
        help=("Modality"),
        type=str,
        default=None,
        required=True,
    )
    subparser_required.add_argument(
        "-r",
        metavar="REGION",
        help=("Region"),
        type=str,
        default=None,
        required=True,
    )

    return subparser


def validate_find_args(parser, args):
    # if everything is valid the run_find
    # get paramters
    fn = args.yaml
    m = args.m
    r = args.r
    o = args.o

    rt = args.rtype

    # load spec
    spec = load_spec(fn)

    # run function
    if rt:
        regions = run_find_by_type(spec, m, r)
    else:
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


def run_find_by_type(spec: Assay, modality: str, region_type: str):
    m = spec.get_modality(modality)
    regions = m.get_region_by_type(region_type)
    return regions

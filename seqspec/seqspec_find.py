from seqspec.utils import load_spec
from seqspec.Assay import Assay
import yaml
import argparse
import warnings
from argparse import RawTextHelpFormatter
from seqspec.seqspec_file import list_files


def setup_find_args(parser):
    subparser = parser.add_parser(
        "find",
        description="""
Find objects in the spec.

Examples:
seqspec find -m rna -s read -i rna_R1 spec.yaml         # Find reads by id
seqspec find -m rna -s region-type -i barcode spec.yaml # Find regions with barcode region type
seqspec find -m rna -s file -i r1.fastq.gz spec.yaml    # Find files with id r1.fastq.gz
---
""",
        help="Find objects in seqspec file",
        formatter_class=RawTextHelpFormatter,
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
    # depracate
    subparser.add_argument("--rtype", help=argparse.SUPPRESS, action="store_true")
    choices = ["read", "region", "file", "region-type"]
    subparser.add_argument(
        "-s",
        metavar="Selector",
        help=(f"Selector, [{','.join(choices)}] (default: region)"),
        type=str,
        default="region",
        choices=choices,
    )
    subparser_required.add_argument(
        "-m",
        metavar="MODALITY",
        help=("Modality"),
        type=str,
        default=None,
        required=True,
    )
    # depracate -r
    subparser_required.add_argument(
        "-r",
        metavar="REGION",
        help=argparse.SUPPRESS,
        type=str,
        default=None,
    )
    subparser_required.add_argument(
        "-i",
        metavar="IDs",
        help=("IDs"),
        type=str,
        default=None,
        required=False,
    )

    return subparser


def validate_find_args(parser, args):
    # IDs
    if args.r is not None:
        warnings.warn(
            "The '-r' argument is deprecated and will be removed in a future version. "
            "Please use '-i' instead.",
            DeprecationWarning,
        )
        # Optionally map the old option to the new one
        if not args.i:
            args.i = args.r

    fn = args.yaml
    m = args.m
    o = args.o
    idtype = args.s  # selector
    ids = args.i

    # run function
    return run_find(fn, m, ids, idtype, o)


def run_find(spec_fn: str, modality: str, id: str, idtype: str, o: str):
    spec = load_spec(spec_fn)
    found = []
    if idtype == "region-type":
        found = find_by_region_type(spec, modality, id)
    elif idtype == "region":
        found = find_by_region_id(spec, modality, id)
    elif idtype == "read":
        found = find_by_read_id(spec, modality, id)
    elif idtype == "file":
        found = find_by_file_id(spec, modality, id)
    else:
        raise ValueError(f"Unknown idtype: {idtype}")

    # post processing
    if o:
        with open(o, "w") as f:
            yaml.dump(found, f, sort_keys=False)
    else:
        print(yaml.dump(found, sort_keys=False))

    return


# TODO implement
def find_by_read_id(spec: Assay, modality: str, id: str):
    rds = []
    reads = spec.get_seqspec(modality)
    for r in reads:
        if r.read_id == id:
            rds.append(r)
    return rds


# TODO implement
def find_by_file_id(spec: Assay, modality: str, id: str):
    files = []
    lf = list_files(spec, modality)
    for k, v in lf.items():
        for f in v:
            if f.file_id == id:
                files.append(f)
    return files


def find_by_region_id(spec: Assay, modality: str, id: str):
    m = spec.get_libspec(modality)
    regions = m.get_region_by_id(id)
    return regions


def find_by_region_type(spec: Assay, modality: str, id: str):
    m = spec.get_libspec(modality)
    regions = m.get_region_by_region_type(id)
    return regions

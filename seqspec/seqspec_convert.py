from seqspec.Region import Region
from seqspec.Assay import Assay
from seqspec.utils import load_spec
import os
from typing import List, Dict


def setup_convert_args(parser):
    parser_convert = parser.add_parser(
        "convert",
        description="convert FASTQ files from spec A to spec B",
        help="convert FASTA files",
    )
    parser_convert.add_argument(
        "-A", metavar="specA", type=str, help="seqspec for assay A"
    )
    parser_convert.add_argument(
        "-B", metavar="specB", type=str, help="seqspec for assay B"
    )
    parser_convert.add_argument(
        "FASTQs",
        help=("list of FASTQ files"),
        nargs="+",
    )
    parser_convert.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
    )
    return parser_convert


def validate_convert_args(parser, args):
    # if everything is valid the run_convert
    A_fn = args.A
    B_fn = args.B
    FQs_fn = args.FASTQs

    o = args.o
    A = load_spec(A_fn)
    B = load_spec(B_fn)

    # load in two specs
    run_convert(A, B, FQs_fn)


def run_convert(A: Assay, B: Assay, FQs_fn: List[str]):
    fastqs = [{os.path.basename(i): i} for i in FQs_fn]
    pass


def convert_regions(R1: Region, R2: Region):
    pass

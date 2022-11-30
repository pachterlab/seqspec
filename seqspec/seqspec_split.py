from seqspec.utils import load_spec, write_read, get_cuts
from collections import defaultdict
from seqspec.seqspec_find import run_find
import os
import gzip
from contextlib import ExitStack


def setup_split_args(parser):
    parser_split = parser.add_parser(
        "split",
        description="split regions in a seqspec file",
        help="split regions in a seqspec file",
    )
    parser_split.add_argument("yaml", help="Sequencing specification yaml file")
    parser_split.add_argument(
        "-o",
        metavar="OUT",
        help=("Folder for output files"),
        type=str,
        default=None,
    )
    parser_split.add_argument(
        "-m",
        metavar="MODALITY",
        help=("Modality"),
        type=str,
        default=None,
    )
    parser_split.add_argument(
        "-r",
        metavar="REGION",
        help=("Region"),
        type=str,
        default=None,
    )
    parser_split.add_argument(
        "-f",
        metavar="FASTQ",
        help=("Fastq"),
        type=str,
        default=None,
    )
    return parser_split


def validate_split_args(parser, args):
    # if everything is valid the run_split
    # get paramters
    fn = args.yaml
    m = args.m
    r = args.r
    o = args.o
    f = args.f

    # load spec
    spec = load_spec(fn)

    # run function
    run_split(spec, m, r, f, o)


def run_split(spec, modality, rid, fname, o=""):
    # given a modality, region, and FASTQ file, separate all of the first level sub regions
    index = defaultdict(list)

    rgn = run_find(spec, modality, rid)[0]
    cuts = get_cuts(rgn.regions)
    # groupby requested region
    for idx, l in enumerate(rgn.regions):
        t = l.region_type
        c = cuts[idx]

        index[t].extend([c])
    # sort the lists within each
    for r, cs in index.items():
        index[r] = sorted(cs, key=lambda tup: tup[0])

    with gzip.open(fname, "rt") as f, ExitStack() as stack:
        outfile = {
            fname: stack.enter_context(
                gzip.open(f"{os.path.join(o, fname)}.fastq.gz", "wt")
            )
            for fname in index.keys()
        }
        lines = []
        for idx, l in enumerate(f):
            lines.append(l.strip())
            if (idx + 1) % 4 != 0:
                continue
            header = lines[0]
            seq = lines[1]
            qual = lines[3]
            for rgn, cs in index.items():
                eseq = ""
                equal = ""
                for c in cs:
                    l, r = c
                    eseq += seq[l:r]
                    equal += qual[l:r]
                write_read(header, eseq, equal, outfile[rgn])
            lines = []

from seqspec.utils import load_spec, get_cuts
from seqspec.seqspec_find import run_find
from collections import defaultdict
from typing import Dict, List, Tuple
from argparse import SUPPRESS
import os


def setup_index_args(parser):
    subparser = parser.add_parser(
        "index",
        description="index regions in a seqspec file",
        help="index regions in a seqspec file",
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

    subparser.add_argument(
        "-s",
        metavar="SUBREGIONTYPE",
        help=SUPPRESS,
        type=str,
        default=None,
    )

    subparser.add_argument(
        "-t",
        metavar="TOOL",
        help=("Tool"),
        default="tab",
        type=str,
        choices=["chromap", "kb", "seqkit", "simpleaf", "starsolo", "tab", "zumis"],
    )

    subparser.add_argument(
        "--rev", help="Returns 3'->5' region order", action="store_true"
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


def validate_index_args(parser, args):
    # if everything is valid the get_index
    # get paramters
    fn = args.yaml
    m = args.m
    r = args.r
    t = args.t
    o = args.o
    s = args.s
    rev = args.rev

    # load spec
    spec = load_spec(fn)
    rgns = r.split(",")
    # regions can be paths, take the basename of the path, use os

    rgns = [os.path.basename(r) for r in rgns]

    x = run_index(spec, m, rgns, fmt=t, rev=rev, subregion_type=s)

    # post processing
    if o:
        with open(o, "w") as f:
            print(x, file=f)
    else:
        print(x)
    return


def run_index(spec, modality, regions, fmt="tab", rev=False, subregion_type=None):
    FORMAT = {
        "chromap": format_chromap,
        "kb": format_kallisto_bus,
        "seqkit": format_seqkit_subseq,
        "simpleaf": format_simpleaf,
        "starsolo": format_starsolo,
        "tab": format_tab,
        "zumis": format_zumis,
    }
    indices = []
    for r in regions:
        index = get_index(spec, modality, r, rev=rev)
        indices.append({r: index})
    return FORMAT[fmt](indices, subregion_type)


def get_index_by_type(
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


def get_index(spec, modality, region_id, rev=False) -> Dict[Tuple[int, int], str]:
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


def format_kallisto_bus(indices, subregion_type=None):
    bcs = []
    umi = []
    feature = []
    for idx, region in enumerate(indices):
        for rgn, index in region.items():
            for k, v in index.items():
                if v.upper() == "BARCODE":
                    bcs.append(f"{idx},{k[0]},{k[1]}")
                elif v.upper() == "UMI":
                    umi.append(f"{idx},{k[0]},{k[1]}")
                elif (
                    v.upper() == "CDNA"
                    or v.upper() == "GDNA"
                    or v.upper() == "PROTEIN"
                    or v.upper() == "TAG"
                ):
                    feature.append(f"{idx},{k[0]},{k[1]}")
    if len(umi) == 0:
        umi.append("-1,-1,-1")
    if len(bcs) == 0:
        bcs.append("-1,-1,-1")

    x = ",".join(bcs) + ":" + ",".join(umi) + ":" + ",".join(feature)
    return x


# this one should only return one string
def format_seqkit_subseq(indices, subregion_type=None):
    # The x string format is start:stop (1-indexed)
    # x = ""
    # region = indices[0]
    # # need to get the right start position
    x = ""
    region = indices[0]
    for rgn, index in region.items():
        for k, v in index.items():
            if v == subregion_type:
                x = f"{k[0]+1}:{k[1]}\n"

    return x


def format_tab(indices, subregion_type=None):
    x = ""
    for idx, region in enumerate(indices):
        for rgn, index in region.items():
            for k, v in index.items():
                x += f"{rgn}\t{v}\t{k[0]}\t{k[1]}\n"

    return x[:-1]


def format_starsolo(indices, subregion_type=None):
    bcs = []
    umi = []
    cdna = []
    for idx, region in enumerate(indices):
        for rgn, index in region.items():
            for k, v in index.items():
                if v.upper() == "BARCODE":
                    bcs.append(f"--soloCBstart {k[0] + 1} --soloCBlen {k[1]}")
                elif v.upper() == "UMI":
                    umi.append(f"--soloUMIstart {k[0] + 1} --soloUMIlen {k[1] - k[0]}")
                elif v.upper() == "CDNA":
                    cdna.append(f"{k[0]},{k[1]}")
    x = f"--soloType CB_UMI_Simple {bcs[0]} {umi[0]}"
    return x


def format_simpleaf(indices, subregion_type=None):
    x = ""
    xl = []
    for idx, region in enumerate(indices):
        fn = idx
        x = f"{fn+1}{{"
        for rgn, index in region.items():
            for k, v in index.items():
                if v.upper() == "BARCODE":
                    x += f"b[{k[1]-k[0]}]"
                elif v.upper() == "UMI":
                    x += f"u[{k[1]-k[0]}]"
                elif v.upper() == "CDNA":
                    x += f"r[{k[1] - k[0]}]"
            x += "x:}"
        xl.append(x)
    return "".join(xl)


def format_zumis(indices, subregion_type=None):
    xl = []
    for idx, region in enumerate(indices):
        x = ""
        for rgn, index in region.items():
            for k, v in index.items():
                if v.upper() == "BARCODE":
                    x += f"- BCS({k[0] + 1}-{k[1]})\n"
                elif v.upper() == "UMI":
                    x += f"- UMI({k[0] + 1}-{k[1]})\n"
                elif v.upper() == "CDNA":
                    x += f"- cDNA({k[0] + 1}-{k[1]})\n"
        xl.append(x)

    return "\n".join(xl)[:-1]


def format_chromap(indices, subregion_type=None):
    bc_fqs = []
    bc_str = []
    gdna_fqs = []
    gdna_str = []
    for idx, region in enumerate(indices):
        for rgn, index in region.items():
            for k, v in index.items():
                if v.upper() == "BARCODE":
                    bc_fqs.append(rgn)
                    bc_str.append(f"bc:{k[0]}:{k[1]}")
                    pass
                elif v.upper() == "GDNA":
                    gdna_fqs.append(rgn)
                    gdna_str.append(f"{k[0]}:{k[1]}")
    if len(set(bc_fqs)) > 1:
        raise "chromap only supports barcodes from one fastq"
    if len(set(gdna_fqs)) > 2:
        raise "chromap only supports genomic dna from two fastqs"

    barcode_fq = bc_fqs[0]
    read1_fq = list(set(gdna_fqs))[0]
    read2_fq = list(set(gdna_fqs))[1]
    read_str = ",".join([f"r{idx}:{ele}" for idx, ele in enumerate(gdna_str, 1)])
    bc_str = ",".join(bc_str)

    cmap_str = f"-1 {read1_fq} -2 {read2_fq} --barcode {barcode_fq} --read-format {bc_str},{read_str}"

    return cmap_str


def format_splitcode(indices, subregion_type=None):
    pass

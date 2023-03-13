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
        "-t",
        metavar="TOOL",
        help=("Tool"),
        type=str,
        default="tab",
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
    t = args.t
    o = args.o
    rev = args.rev

    # load spec
    spec = load_spec(fn)
    rgns = r.split(",")

    indices = []
    for r in rgns:
        index = run_index(spec, m, r, rev=rev)
        indices.append({r: index})

    FORMAT = {
        "kb": format_kallisto_bus,
        "starsolo": format_starsolo,
        "tab": format_tab,
        "simpleaf": format_simpleaf,
        "zumis": format_zumis,
    }
    # post processing
    if o:
        with open(o, "w") as f:
            print(FORMAT[t](indices), file=f)
    else:
        print(FORMAT[t](indices))


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


def format_kallisto_bus(indices):
    bcs = []
    umi = []
    cdna = []
    for idx, region in enumerate(indices):
        for rgn, index in region.items():
            for k, v in index.items():
                if v == "barcode":
                    bcs.append(f"{idx},{k[0]},{k[1]}")
                elif v == "umi":
                    umi.append(f"{idx},{k[0]},{k[1]}")
                elif v == "cDNA":
                    cdna.append(f"{idx},{k[0]},{k[1]}")

    x = "&".join(bcs) + ":" + "&".join(umi) + ":" + "&".join(cdna)
    return x


def format_tab(indices):
    x = ""
    for idx, region in enumerate(indices):
        for rgn, index in region.items():
            for k, v in index.items():
                x += f"{rgn}\t{v}\t{k[0]}\t{k[1]}\n"

    return x[:-1]


def format_starsolo(indices):
    bcs = []
    umi = []
    cdna = []
    for idx, region in enumerate(indices):
        for rgn, index in region.items():
            for k, v in index.items():
                if v == "barcode":
                    bcs.append(f"--soloCBstart {k[0] + 1} --soloCBlen {k[1]}")
                elif v == "umi":
                    umi.append(f"--soloUMIstart {k[0] + 1} --soloUMIlen {k[1] - k[0]}")
                elif v == "cDNA":
                    cdna.append(f"{k[0]},{k[1]}")
    x = f"--soloType CB_UMI_Simple {bcs[0]} {umi[0]}"
    return x


def format_simpleaf(indices):
    x = ""
    xl = []
    for idx, region in enumerate(indices):
        fn = idx
        x = f"{fn+1}{{"
        for rgn, index in region.items():
            for k, v in index.items():
                if v == "barcode":
                    x += f"b[{k[1]-k[0]}]"
                elif v == "umi":
                    x += f"u[{k[1]-k[0]}]"
                elif v == "cDNA":
                    x += f"r[{k[1] - k[0]}]"
            x += "x:}"
        xl.append(x)
    return "".join(xl)


def format_zumis(indices):
    xl = []
    for idx, region in enumerate(indices):
        x = ""
        for rgn, index in region.items():
            for k, v in index.items():
                if v == "barcode":
                    x += f"- BCS({k[0] + 1}-{k[1]})\n"
                elif v == "umi":
                    x += f"- UMI({k[0] + 1}-{k[1]})\n"
                elif v == "cDNA":
                    x += f"- cDNA({k[0] + 1}-{k[1]})\n"
        xl.append(x)

    return "\n".join(xl)[:-1]

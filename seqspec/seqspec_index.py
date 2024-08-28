from seqspec.utils import load_spec, map_read_id_to_regions
from seqspec.seqspec_find import run_find
import warnings
from collections import defaultdict
from typing import List, Dict

# from typing import Dict, List
from argparse import SUPPRESS
import os
from seqspec.Region import (
    project_regions_to_coordinates,
    itx_read,
    ReadCoordinate,
)


def setup_index_args(parser):
    subparser = parser.add_parser(
        "index",
        description="index reads or regions in a seqspec file",
        help="index reads or regions in a seqspec file",
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
        "--subregion_type",
        metavar="SUBREGIONTYPE",
        help=SUPPRESS,
        type=str,
        default=None,
    )

    choices = ["chromap", "kb", "seqkit", "simpleaf", "starsolo", "tab", "zumis"]
    subparser.add_argument(
        "-t",
        metavar="TOOL",
        help=(f"Tool, [{','.join(choices)}] (default: tab)"),
        default="tab",
        type=str,
        choices=["chromap", "kb", "seqkit", "simpleaf", "starsolo", "tab", "zumis"],
    )
    # the object we are using to index
    choices = ["read", "region", "file"]
    subparser.add_argument(
        "-c",
        metavar="CLASS",
        help=(f"Class, [{','.join(choices)}] (default: read)"),
        type=str,
        default="read",
        choices=["read", "region", "file"],
    )
    subparser.add_argument(
        "--list-files",
        help="List files",
        type=str,
        default=None,
        choices=["paired", "interleaved", "index"],
    )
    subparser.add_argument(
        "--rev", help="Returns 3'->5' region order", action="store_true"
    )

    # boolean to indicate specifying a region or a read
    subparser.add_argument(
        "--region",
        action="store_true",
        help=SUPPRESS,
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
        "-i",
        metavar="IDs",
        help=("IDs"),
        type=str,
        default=None,
        required=False,
    )
    subparser_required.add_argument(
        "-r",
        metavar="READ or REGION or FILE",
        help=SUPPRESS,
        type=str,
    )

    return subparser


# nested index command
# seqspec index -c file -t kb -m rna -i \
# "$(seqspec index --list-files index -c file -t kb -m rna \
# -i "rna_R2_SRR18677638.fastq.gz,rna_R1_SRR18677638.fastq.gz" spec.yaml)" \
# spec.yaml
def validate_index_args(parser, args):
    if args.r is not None:
        warnings.warn(
            "The '-r' argument is deprecated and will be removed in a future version. "
            "Please use '-i' instead.",
            DeprecationWarning,
        )
        # Optionally map the old option to the new one
        if not args.i:
            args.i = args.r

    # if everything is valid the get_index
    # get paramters
    fn = args.yaml
    m = args.m
    ids = args.i  # this can be a list of ids (reads, regions, or files)
    t = args.t
    o = args.o
    subregion_type = args.subregion_type
    rev = args.rev
    list_files = args.list_files

    idtype = args.c

    # load spec
    spec = load_spec(fn)
    ids = ids.split(",")
    # ids can be paths, take the basename of the path, use os
    if idtype == "file" or idtype == "read":
        ids = [os.path.basename(r) for r in ids]
    elif idtype == "region":
        ids = ids

    if list_files is not None:
        x = run_list_files(spec, m, ids, idtype=idtype, fmt=list_files)
    else:
        x = run_index(
            spec, m, ids, idtype, fmt=t, rev=rev, subregion_type=subregion_type
        )

    # post processing
    if o:
        with open(o, "w") as f:
            print(x, file=f)
    else:
        print(x)
    return


def run_index(
    spec,
    modality,
    ids,
    idtype="read",
    fmt="tab",
    rev=False,
    subregion_type=None,
):
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
    if idtype == "file":
        indices = get_index_by_files(spec, modality, ids)
    else:
        for id in ids:
            if idtype == "region":
                index = get_index(spec, modality, id, rev=rev)
            elif idtype == "read":
                index = get_index_by_primer(spec, modality, id)
            indices.append(index)
    return FORMAT[fmt](indices, subregion_type)


# seqspec index -c file -t kb -m rna -i "rna_R2_SRR18677638.fastq.gz,rna_R1_SRR18677638.fastq.gz" spec.yaml
def get_index_by_files(spec, modality, file_ids):
    # get the read associated for each file for each read get the regions by mapping primer

    files = list_files_by_file_id(spec, modality, file_ids)

    # iterate through the keys (read ids) and get the index for each read
    indices = []
    for k, v in files.items():
        index = get_index_by_primer(spec, modality, k)
        indices.append(index)
    return indices


def format_list_files(files: Dict[str, List[str]], fmt):
    # input dict of read id to list of files
    x = ""
    if fmt == "paired":
        for items in zip(*files.values()):
            f = "\t".join(items)
            x += f"{f}\n"
        x = x[:-1]

    elif fmt == "interleaved":
        for items in zip(*files.values()):
            for item in items:
                x += item + "\n"
        x = x[:-1]
    elif fmt == "index":
        for items in zip(*files.values()):
            for item in items:
                x += item + ","
        x = x[:-1]
    return x


# seqspec index --list-files paired -c file -t kb -m rna -i "rna_R2_SRR18677638.fastq.gz,rna_R1_SRR18677638.fastq.gz" spec.yaml
def run_list_files(spec, modality, ids, idtype="read", fmt="paired"):
    # first get the files associated with each id
    # NOTE: LIST FILES DOES NOT RESPECT ORDERING OF INPUT IDs LIST
    if idtype == "read":
        files = list_files_by_read_id(spec, modality, ids)
    elif idtype == "file":
        files = list_files_by_file_id(spec, modality, ids)
    x = format_list_files(files, fmt)
    return x


def list_files_by_read_id(spec, modality, read_ids):
    seqspec = spec.get_seqspec(modality)
    files = defaultdict(list)
    ids = set(read_ids)
    # TODO return the files in the order of the ids given in the input
    # NOTE ORDERING HERE IS IMPORANT SEE GET_INDEX_BY_FILES FUNCTION
    for read in seqspec:
        if read.read_id in ids:
            for file in read.files:
                files[read.read_id].append(file.filename)
    return files


def list_files_by_file_id(spec, modality, file_ids):
    seqspec = spec.get_seqspec(modality)
    ids = set(file_ids)
    files = defaultdict(list)
    # TODO: NOTE ORDERING HERE IS IMPORTANT SEE RUN_LIST_FILES FUNCTION
    for read in seqspec:
        for file in read.files:
            if file.filename in ids:
                files[read.read_id].append(file.filename)
    return files


# TODO fix return type
def get_index(
    spec, modality, region_id, rev=False
):  # -> Dict[str, List[RegionCoordinate]]:
    rid = region_id
    regions = run_find(spec, modality, rid)
    leaves = regions[0].get_leaves()
    if rev:
        leaves.reverse()
    cuts = project_regions_to_coordinates(leaves)

    return {region_id: cuts, "strand": "pos"}


# TODO fix return type
def get_index_by_primer(
    spec, modality: str, read_id: str
):  # -> Dict[str, List[RegionCoordinate]]:  # noqa
    # this manages the strandedness internally
    (read, rgns) = map_read_id_to_regions(spec, modality, read_id)

    # get the cuts for all of the atomic elements (tuples of 0-indexed start stop)
    rcs = project_regions_to_coordinates(rgns)

    new_rcs = itx_read(rcs, 0, read.max_len)
    rdc = ReadCoordinate(read, new_rcs)

    return {read_id: new_rcs, "strand": rdc.read.strand}


def format_kallisto_bus(indices, subregion_type=None):
    bcs = []
    umi = []
    feature = []
    for idx, region in enumerate(indices):
        rg_strand = region.pop("strand")  # noqa
        for rgn, cuts in region.items():
            for cut in cuts:
                if cut.region_type.upper() == "BARCODE":
                    bcs.append(f"{idx},{cut.start},{cut.stop}")
                elif cut.region_type.upper() == "UMI":
                    umi.append(f"{idx},{cut.start},{cut.stop}")
                elif (
                    cut.region_type.upper() == "CDNA"
                    or cut.region_type.upper() == "GDNA"
                    or cut.region_type.upper() == "PROTEIN"
                    or cut.region_type.upper() == "TAG"
                ):
                    feature.append(f"{idx},{cut.start},{cut.stop}")
    if len(umi) == 0:
        umi.append("-1,-1,-1")
    if len(bcs) == 0:
        bcs.append("-1,-1,-1")

    x = ",".join(bcs) + ":" + ",".join(umi) + ":" + ",".join(feature)
    return x


# this one should only return one string
# TODO: return to this
def format_seqkit_subseq(indices, subregion_type=None):
    # The x string format is start:stop (1-indexed)
    # x = ""
    # region = indices[0]
    # # need to get the right start position
    x = ""
    region = indices[0]
    for rgn, cuts in region.items():
        for cut in cuts:
            if cut.region_type == subregion_type:
                x = f"{cut.start+1}:{cut.stop}\n"

    return x


def format_tab(indices, subregion_type=None):
    x = ""
    for idx, region in enumerate(indices):
        rg_strand = region.pop("strand")  # noqa
        for rgn, cuts in region.items():
            for cut in cuts:
                x += f"{rgn}\t{cut.name}\t{cut.region_type}\t{cut.start}\t{cut.stop}\n"

    return x[:-1]


def format_starsolo(indices, subregion_type=None):
    bcs = []
    umi = []
    cdna = []
    for idx, region in enumerate(indices):
        rg_strand = region.pop("strand")  # noqa
        for rgn, cuts in region.items():
            for cut in cuts:
                if cut.region_type.upper() == "BARCODE":
                    bcs.append(f"--soloCBstart {cut.start + 1} --soloCBlen {cut.stop}")
                elif cut.region_type.upper() == "UMI":
                    umi.append(
                        f"--soloUMIstart {cut.start + 1} --soloUMIlen {cut.stop - cut.start}"
                    )
                elif cut.region_type.upper() == "CDNA":
                    cdna.append(f"{cut.start},{cut.stop}")
    x = f"--soloType CB_UMI_Simple {bcs[0]} {umi[0]}"
    return x


def format_simpleaf(indices, subregion_type=None):
    x = ""
    xl = []
    for idx, region in enumerate(indices):
        rg_strand = region.pop("strand")  # noqa
        fn = idx
        x = f"{fn+1}{{"
        for rgn, cuts in region.items():
            for cut in cuts:
                if cut.region_type.upper() == "BARCODE":
                    x += f"b[{cut.stop-cut.start}]"
                elif cut.region_type.upper() == "UMI":
                    x += f"u[{cut.stop-cut.start}]"
                elif cut.region_type.upper() == "CDNA":
                    x += f"r[{cut.stop - cut.start}]"
            x += "x:}"
        xl.append(x)
    return "".join(xl)


def format_zumis(indices, subregion_type=None):
    xl = []
    for idx, region in enumerate(indices):
        rg_strand = region.pop("strand")  # noqa
        x = ""
        for rgn, cuts in region.items():
            for cut in cuts:
                if cut.region_type.upper() == "BARCODE":
                    x += f"- BCS({cut.start + 1}-{cut.stop})\n"
                elif cut.region_type.upper() == "UMI":
                    x += f"- UMI({cut.start + 1}-{cut.stop})\n"
                elif cut.region_type.upper() == "CDNA":
                    x += f"- cDNA({cut.start + 1}-{cut.stop})\n"
        xl.append(x)

    return "\n".join(xl)[:-1]


def stable_deduplicate_fqs(fqs):
    # stably deduplicate gdna_fqs
    seen_fqs = set()
    deduplicated_fqs = []
    for r in fqs:
        if r not in seen_fqs:
            deduplicated_fqs.append(r)
            seen_fqs.add(r)
    return deduplicated_fqs


def format_chromap(indices, subregion_type=None):
    bc_fqs = []
    bc_str = []
    gdna_fqs = []
    gdna_str = []
    for idx, region in enumerate(indices):
        rg_strand = region.pop("strand")
        print(rg_strand)
        strand = "" if rg_strand == "pos" else ":-"
        for rgn, cuts in region.items():
            for cut in cuts:
                if cut.region_type.upper() == "BARCODE":
                    bc_fqs.append(rgn)
                    bc_str.append(f"bc:{cut.start}:{cut.stop-1}{strand}")
                    pass
                elif cut.region_type.upper() == "GDNA":
                    gdna_fqs.append(rgn)
                    gdna_str.append(f"{cut.start}:{cut.stop-1}")
    if len(set(bc_fqs)) > 1:
        raise Exception("chromap only supports barcodes from one fastq")
    if len(set(gdna_fqs)) > 2:
        raise Exception("chromap only supports genomic dna from two fastqs")

    barcode_fq = bc_fqs[0]
    deduplicated_gdna_fqs = stable_deduplicate_fqs(gdna_fqs)
    read1_fq = deduplicated_gdna_fqs[0]
    read2_fq = deduplicated_gdna_fqs[1]
    read_str = ",".join([f"r{idx}:{ele}" for idx, ele in enumerate(gdna_str, 1)])
    bc_str = ",".join(bc_str)

    cmap_str = f"-1 {read1_fq} -2 {read2_fq} --barcode {barcode_fq} --read-format {bc_str},{read_str}"

    return cmap_str


def format_splitcode(indices, subregion_type=None):
    pass

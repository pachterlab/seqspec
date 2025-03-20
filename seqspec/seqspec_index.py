from seqspec.utils import load_spec, map_read_id_to_regions
from seqspec.seqspec_find import find_by_region_id
import warnings
from seqspec.seqspec_file import list_files_by_file_id, list_read_files
from argparse import SUPPRESS, RawTextHelpFormatter
from seqspec.Region import complement_sequence
from seqspec.Region import RegionCoordinateDifference

from seqspec.Region import (
    project_regions_to_coordinates,
    itx_read,
)
from seqspec.Read import ReadCoordinate


def setup_index_args(parser):
    subparser = parser.add_parser(
        "index",
        description="""
Identify the position of elements in a spec for use in downstream tools.

Examples:
seqspec index -m rna -s file -t kb spec.yaml                              # Index file elements in kallisto bustools format
seqspec index -m rna -s file spec.yaml                                    # Index file elements corresponding to reads
seqspec index -m rna -s read -i rna_R1 spec.yaml                          # Index read elements in rna_R1
seqspec index -m rna -s file -i rna_R1.fastq.gz,rna_R2.fastq.gz spec.yaml # Index file elements in rna reads
---
""",
        help="Identify position of elements in seqspec file",
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

    subparser.add_argument(
        "--subregion_type",
        metavar="SUBREGIONTYPE",
        help=SUPPRESS,
        type=str,
        default=None,
    )

    choices = [
        "chromap",
        "kb",
        "relative",
        "seqkit",
        "simpleaf",
        "starsolo",
        "splitcode",
        "tab",
        "zumis",
    ]
    subparser.add_argument(
        "-t",
        metavar="TOOL",
        help=(f"Tool, [{', '.join(choices)}] (default: tab)"),
        default="tab",
        type=str,
        choices=choices,
    )
    # the object we are using to index
    choices = ["read", "region", "file"]
    subparser.add_argument(
        "-s",
        metavar="SELECTOR",
        help=(f"Selector for ID, [{', '.join(choices)}] (default: read)"),
        type=str,
        default="read",
        choices=choices,
    )
    subparser.add_argument(
        "--rev", help="Returns 3'->5' region order", action="store_true"
    )

    # boolean to indicate specifying a region or a read
    # depracate
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
    if args.region:
        warnings.warn(
            "The '--region' argument is deprecated and will be removed in a future version. "
            "Please use '-s region' instead.",
            DeprecationWarning,
        )

    fn = args.yaml
    m = args.m
    ids = args.i  # this can be a list of ids (reads, regions, or files)
    t = args.t
    o = args.o
    subregion_type = args.subregion_type
    rev = args.rev
    idtype = args.s

    if ids is None and (idtype == "read" or idtype == "region"):
        parser.error("Must specify ids with -i for -s read or -s region")

    return run_index(fn, m, ids, idtype, t, rev, subregion_type, o=o)


def run_index(
    spec_fn,
    modality,
    ids,
    idtype,
    fmt,
    rev,
    subregion_type,
    o,
):
    spec = load_spec(spec_fn)
    if ids is None:
        ids = []
    else:
        ids = ids.split(",")

    x = index(spec, modality, ids, idtype, fmt, rev, subregion_type)

    # post processing
    if o:
        with open(o, "w") as f:
            print(x, file=f)
    else:
        print(x)

    return x


def index(
    spec,
    modality,
    ids,
    idtype,
    fmt,
    rev=False,
    subregion_type=None,
):
    FORMAT = {
        "chromap": format_chromap,
        "kb": format_kallisto_bus,
        "relative": format_relative,
        "seqkit": format_seqkit_subseq,
        "simpleaf": format_simpleaf,
        "starsolo": format_starsolo,
        "splitcode": format_splitcode,
        "tab": format_tab,
        "zumis": format_zumis,
    }

    GET_INDICES = {
        "file": get_index_by_files,
    }

    GET_INDICES_BY_IDS = {
        "file": get_index_by_file_ids,
        "region": get_index_by_region_ids,
        "read": get_index_by_read_ids,
    }

    if len(ids) == 0:
        indices = GET_INDICES[idtype](spec, modality)
    else:
        indices = GET_INDICES_BY_IDS[idtype](spec, modality, ids)

    return FORMAT[fmt](spec, indices, subregion_type)


def get_index_by_files(spec, modality):
    # get the read associated for each file for each read get the regions by mapping primer
    files = list_read_files(spec, modality)

    # iterate through the keys (read ids) and get the index for each read
    indices = []
    for k, v in files.items():
        index = get_index_by_primer(spec, modality, k)
        indices.append(index)
    return indices


def get_index_by_file_ids(spec, modality, file_ids):
    # get the read associated for each file for each read get the regions by mapping primer
    files = list_files_by_file_id(spec, modality, file_ids)

    # iterate through the keys (read ids) and get the index for each read
    indices = []
    for k, v in files.items():
        index = get_index_by_primer(spec, modality, k)
        indices.append(index)
    return indices


def get_index_by_region_ids(spec, modality, region_ids):
    indices = []
    for id in region_ids:
        index = get_index_by_primer(spec, modality, id)
        indices.append(index)
    return indices


def get_index_by_read_ids(spec, modality, read_ids):
    indices = []
    for id in read_ids:
        index = get_index_by_primer(spec, modality, id)
        indices.append(index)
    return indices


# TODO fix return type
def get_index(
    spec, modality, region_id, rev=False
):  # -> Dict[str, List[RegionCoordinate]]:
    rid = region_id
    regions = find_by_region_id(spec, modality, rid)
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


def format_kallisto_bus(spec, indices, subregion_type=None):
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
def format_seqkit_subseq(spec, indices, subregion_type=None):
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


def format_tab(spec, indices, subregion_type=None):
    x = ""
    for idx, region in enumerate(indices):
        rg_strand = region.pop("strand")  # noqa
        for rgn, cuts in region.items():
            for cut in cuts:
                x += f"{rgn}\t{cut.name}\t{cut.region_type}\t{cut.start}\t{cut.stop}\n"

    return x[:-1]


def format_starsolo(spec, indices, subregion_type=None):
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


def format_simpleaf(spec, indices, subregion_type=None):
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


def format_zumis(spec, indices, subregion_type=None):
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


    bc_fqs = []
def format_chromap(spec, indices, subregion_type=None):
    bc_str = []
    gdna_fqs = []
    gdna_str = []
    for idx, region in enumerate(indices):
        rg_strand = region.pop("strand")
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


# input is a list of region coordinates
def compute_relative(rcs):
    d = []

    # for cut in rcs:
    #     if cut.sequence_type == "fixed":
    #         fixed.append(cut)
    for rgnc1 in rcs:
        for rgnc2 in rcs:
            diff = rgnc1 - rgnc2
            # obj - fixed
            d.append(RegionCoordinateDifference(rgnc1, rgnc2, diff))

    return d


def filter_differences(d, filter_region_type="linker"):
    f = []
    for rcd in d:
        # print(rcd.rgnc1.region_type, rcd.rgnc2.region_type)
        if (
            rcd.obj.region_type != filter_region_type
            and rcd.fixed.region_type == filter_region_type
        ):
            f.append(rcd)
    return f


def filter_groupby_region_type(g, keep=["umi", "barcode", "cdna"]):
    for k in list(g.keys()):
        if g[k]["obj"].region_type.lower() not in keep:
            g.pop(k)
    return g


def format_relative(spec, indices, subregion_type=None):
    x = ""
    d = []
    for idx, region in enumerate(indices):
        rg_strand = region.pop("strand")  # noqa
        for rgn, cuts in region.items():
            d = compute_relative(cuts)
            f = filter_differences(d)
            f.sort(key=lambda x: x.rgnc1.region_type)

            for i in f:
                x += f"{i.rgnc1.region_id}\t{i.rgnc2.region_id}\t{i.rgncdiff.start}\t{i.rgncdiff.stop}\t{i.loc}\n"
    return x


# todo: return an object of the fixed sequence, cut sequence, and diff. pass this to the format function for splitcode
def group_diff(d):
    # Initialize a dictionary to store objects and their corresponding fixed regions
    obj_dict = {}

    # Group fixed sequences by their obj
    for entry in d:
        obj = entry["obj"]
        fixed = entry["fixed"]
        diff = entry["diff"]
        loc = entry["loc"]

        # Create a list of fixed sequences if obj is encountered for the first time
        if obj.region_id not in obj_dict:
            obj_dict[obj.region_id] = (obj, [])

        # Append fixed sequences with their diff and loc
        obj_dict[obj.region_id][1].append(
            {"obj": obj, "fixed": fixed, "diff": diff, "loc": loc}
        )
    return obj_dict


def groupby_region_id(rgns):
    d = {}
    for rgn in rgns:
        if rgn.obj.region_id not in d:
            d[rgn.obj.region_id] = {"obj": rgn.obj, "rgncdiffs": []}
        d[rgn.obj.region_id]["rgncdiffs"].append(rgn)

    return d


def groupby_region_type(rgns):
    d = {}
    for rgn in rgns:
        if rgn.obj.region_type not in d:
            d[rgn.obj.region_type] = {"obj": rgn.obj, "rgncdiffs": []}
        d[rgn.obj.region_type]["rgncdiffs"].append(rgn)
    return d


# def group_regions_by_region_type(rgns):


def format_splitcode_row(obj, rgncdiffs, idx=0, rev=False, complement=False):
    # print(obj.region_id, idx)
    # TODO only have one object left and one object right of the sequence
    e = ""
    if obj.region_type == "cdna":
        if rev and not complement:
            e += f"<r_{obj.region_id}>"
        elif rev and complement:
            e += f"<~rc_{obj.region_id}>"
        elif not rev and complement:
            e += f"<~c_{obj.region_id}>"
        elif not rev and not complement:
            e += f"<f_{obj.region_id}>"

        if idx == 0:
            e = "0:0" + e
        elif idx == -1:
            e = e + "0:-1"
    else:
        if rev and not complement:
            e += f"<r_{obj.region_type}[{obj.min_len}]>"
        elif rev and complement:
            e += f"<~rc_{obj.region_type}[{obj.min_len}]>"
        elif not rev and complement:
            e += f"<~c_{obj.region_type}[{obj.min_len}]>"
        elif not rev and not complement:
            e += f"<f_{obj.region_type}[{obj.min_len}]>"

    # iterate the region coordinate differences
    p1 = False
    m1 = False
    srtdiffs = sorted(rgncdiffs, key=lambda x: x.rgncdiff.min_len)
    for diffs in srtdiffs:
        obj = diffs.obj
        fixed = diffs.fixed
        loc = diffs.loc
        diff = diffs.rgncdiff
        if fixed.region_type == "linker":
            minl = diff.min_len
            if minl == 0:
                minl = ""
            if loc == "+" and not p1:
                if rev and not complement:
                    e = e + f"{minl}{{{fixed.region_id}r}}"
                elif rev and complement:
                    e = e + f"{minl}{{{fixed.region_id}rc}}"
                elif not rev and complement:
                    e = f"{{{fixed.region_id}c}}{minl}" + e
                elif not rev and not complement:
                    e = f"{{{fixed.region_id}f}}{minl}" + e
                p1 = True
            elif loc == "-" and not m1:
                if rev and not complement:
                    e = f"{{{fixed.region_id}r}}{minl}" + e
                elif rev and complement:
                    e = f"{{{fixed.region_id}rc}}{minl}" + e
                elif not rev and complement:
                    e = e + f"{minl}{{{fixed.region_id}c}}"
                elif not rev and not complement:
                    e = e + f"{minl}{{{fixed.region_id}f}}"
                m1 = True
    return {"region_type": obj.region_type, "fmt": e}


def format_splitcode(spec, indices, subregion_type=None):
    # extraction based on fixed sequences
    # extraction based on onlist sequences
    # umi - bc3 - link2 - bc2 - link1 - bc1 - read
    # @extract <f_umi[10]>8{linker2f},<f_bc[8]>{linker2f},{linker2f}<f_bc[8]>{linker1f},{linker1f}<f_bc[8]>,{linker1f}8<f_read>0:-1
    # @extract 0:0<r_read>14{linker1r},<r_bc[8]>{linker1r},{linker1r}<r_bc[8]>{linker2r},{linker2r}<r_bc[8]>,{linker2r}8<r_umi[10]>
    # @extract <~c_umi[10]>8{linker2c},<~c_bc[8]>{linker2c},{linker2c}<~c_bc[8]>{linker1c},{linker1c}<~c_bc[8]>,{linker1c}8<~c_read>0:-
    # @extract 0:0<~rc_read>14{linker1rc},<~rc_bc[8]>{linker1rc},{linker1rc}<~rc_bc[8]>{linker2rc},{linker2rc}<~rc_bc[8]>,{linker2rc}8<~rc_umi[10]>#

    # format the positions
    x = ""
    e = ""
    d = []
    coords = indices
    for idx, coord in enumerate(coords):
        rg_strand = coord.pop("strand")  # noqa

        # iterate through the read id
        for coord_id, cuts in coord.items():
            # object, fixed sequence, diff
            d = compute_relative(cuts)

            # retain only the "objects" that are not linkers
            f = filter_differences(d)

            # groupby region_id of the first object (order is retained wrt library)
            g = groupby_region_id(f)

            # remove everything from g except obj.region_type umi/cdna/barcode
            g = filter_groupby_region_type(g)

            g = list(g.values())

            # format forward rows
            frows = []
            rrows = []
            crows = []
            rcrows = []
            for idx, (gb, rgb) in enumerate(zip(g, g[::-1])):
                if idx + 1 == len(g):
                    idx = -1
                    # format each region_id object
                frows.append(
                    format_splitcode_row(
                        gb["obj"],
                        gb["rgncdiffs"],
                        idx,
                        rev=False,
                        complement=False,
                    )
                )
                rrows.append(
                    format_splitcode_row(
                        rgb["obj"], rgb["rgncdiffs"], idx, rev=True, complement=False
                    )
                )
                crows.append(
                    format_splitcode_row(
                        gb["obj"], gb["rgncdiffs"], idx, rev=False, complement=True
                    )
                )
                rcrows.append(
                    format_splitcode_row(
                        rgb["obj"], rgb["rgncdiffs"], idx, rev=True, complement=True
                    )
                )

            from collections import defaultdict

            g_frows = defaultdict(list)
            g_crows = defaultdict(list)
            g_rrows = defaultdict(list)
            g_rcrows = defaultdict(list)
            for r in frows:
                g_frows[r["region_type"]].append(r["fmt"])
            for r in crows:
                g_crows[r["region_type"]].append(r["fmt"])
            for r in rrows:
                g_rrows[r["region_type"]].append(r["fmt"])
            for r in rcrows:
                g_rcrows[r["region_type"]].append(r["fmt"])

            for gr in g_frows:
                e += f"@extract {','.join(g_frows[gr])}\n"
            for gr in g_crows:
                e += f"@extract {','.join(g_crows[gr])}\n"
            for gr in g_rrows:
                e += f"@extract {','.join(g_rrows[gr])}\n"
            for gr in g_rcrows:
                e += f"@extract {','.join(g_rcrows[gr])}\n"

    x += e

    # format the parameters
    # groups	ids	tags	distances	locations
    # group1	linker1f	ATCCACGTGCTTGAGACTGTGG	3:3:3	0:0:0 # forward
    # group1	linker1r	GGTGTCAGAGTTCGTGCACCTA	3:3:3	0:0:0 # reverse
    # group1	linker1c	TAGGTGCACGAACTCTGACACC	3:3:3	0:0:0 # complement
    # group1	linker1rc	CCACAGTCTCAAGCACGTGGAT	3:3:3	0:0:0 # reverse complement#

    # group2	linker2f	GTGGCCGATGTTTCGCATCGGCGTACGACT	3:3:3	0:0:0
    # group2	linker2r	TCAGCATGCGGCTACGCTTTGTAGCCGGTG	3:3:3	0:0:0
    # group2	linker2c	CACCGGCTACAAAGCGTAGCCGCATGCTGA	3:3:3	0:0:0
    # group2	linker2rc	AGTCGTACGCCGATGCGAAACATCGGCCAC	3:3:3	0:0:0

    for idx, region in enumerate(indices):
        # rg_strand = region.pop("strand")  # noqa
        lc = ""
        x += "groups\tids\ttags\tdistances\tlocations\n"
        idx = 1
        for rgn, cuts in region.items():
            for cut in cuts:
                lc += f"{cut.name}[{cut.min_len}]\t{cut.sequence}\n"
                if cut.region_type == "linker":
                    # forward, regular and complement
                    x += f"group{idx}\t{cut.name}f\t{cut.sequence}\t3:3:3\t0:0:0\n"
                    x += f"group{idx}\t{cut.name}c\t{complement_sequence(cut.sequence)}\t3:3:3\t0:0:0\n"

                    # reverse, regular and complement
                    x += (
                        f"group{idx}\t{cut.name}r\t{cut.sequence[::-1]}\t3:3:3\t0:0:0\n"
                    )
                    x += f"group{idx}\t{cut.name}rc\t{complement_sequence(cut.sequence)[::-1]}\t3:3:3\t0:0:0\n"
                    idx += 1
    return x

"""Index module for seqspec CLI.

This module provides functionality to identify the position of elements in a spec for use in downstream tools.
"""

import warnings
from argparse import SUPPRESS, ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel

from seqspec.Assay import Assay
from seqspec.Region import (
    RegionCoordinate,
    RegionCoordinateDifference,
    complement_sequence,
    itx_read,
    project_regions_to_coordinates,
)
from seqspec.seqspec_file import list_files_by_file_id
from seqspec.seqspec_find import find_by_region_id
from seqspec.utils import load_spec, map_read_id_to_regions


class Coordinate(BaseModel):
    # query_obj: Union[File, Read, Region]
    query_id: str
    query_name: str
    query_type: str
    rcv: List[RegionCoordinate]
    strand: str = "pos"


def setup_index_args(parser) -> ArgumentParser:
    """Create and configure the index command subparser."""
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
    subparser.add_argument("yaml", help="Sequencing specification yaml file", type=Path)
    subparser.add_argument(
        "-o",
        "--output",
        metavar="OUT",
        help="Path to output file",
        type=Path,
        default=None,
    )

    subparser.add_argument(
        "--subregion-type",
        metavar="SUBREGIONTYPE",
        help=SUPPRESS,
        type=str,
        default=None,
    )

    choices = [
        "chromap",
        "kb",
        "kb-single",
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
        "--tool",
        metavar="TOOL",
        help=f"Tool, [{', '.join(choices)}] (default: tab)",
        default="tab",
        type=str,
        choices=choices,
    )
    # the object we are using to index
    choices = ["read", "region", "file"]
    subparser.add_argument(
        "-s",
        "--selector",
        metavar="SELECTOR",
        help=f"Selector for ID, [{', '.join(choices)}] (default: read)",
        type=str,
        default="read",
        choices=choices,
    )
    subparser.add_argument(
        "--rev", help="Returns 3'->5' region order", action="store_true"
    )

    subparser_required.add_argument(
        "-m",
        "--modality",
        metavar="MODALITY",
        help="Modality",
        type=str,
        required=True,
    )
    subparser_required.add_argument(
        "-i",
        "--ids",
        metavar="IDs",
        help="IDs",
        type=str,
        default=None,
        required=False,
    )

    subparser.add_argument(
        "--no-overlap",
        help="Disable overlap (default: False)",
        action="store_true",
        dest="overlap",
        default=False,
    )

    return subparser


def validate_index_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the index command arguments."""

    if not Path(args.yaml).exists():
        parser.error(f"Input file does not exist: {args.yaml}")

    if args.output and Path(args.output).exists() and not Path(args.output).is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")


def seqspec_index(
    spec: Assay,
    modality: str,
    ids: List[str],
    idtype: str,
    rev: bool = False,
) -> List[Coordinate]:
    """Core functionality to get index information from the spec.

    Args:
        spec: The Assay object to index
        modality: The modality to index
        ids: List of IDs to index
        idtype: Type of ID (read, region, file)
        rev: Whether to return 3'->5' region order

    Returns:
        List of index dictionaries containing region coordinates and strand information
    """
    GET_INDICES = {
        "file": get_index_by_files,
        "read": get_index_by_reads,
        "region": get_index_by_regions,
    }

    GET_INDICES_BY_IDS = {
        "file": get_index_by_file_ids,
        "region": get_index_by_region_ids,
        "read": get_index_by_read_ids,
    }

    if not ids:
        return GET_INDICES[idtype](spec, modality)
    return GET_INDICES_BY_IDS[idtype](spec, modality, ids)


def format_index(
    indices: List[Coordinate], fmt: str, subregion_type: Optional[str] = None
) -> str:
    """Format index information into a specific output format.

    Args:
        indices: List of index dictionaries from seqspec_index
        fmt: Output format to use
        subregion_type: Optional subregion type for filtering

    Returns:
        Formatted index information as a string
    """
    FORMAT = {
        "chromap": format_chromap,
        "kb": format_kallisto_bus,
        "kb-single": format_kallisto_bus_force_single,
        "relative": format_relative,
        "seqkit": format_seqkit_subseq,
        "simpleaf": format_simpleaf,
        "starsolo": format_starsolo,
        "splitcode": format_splitcode,
        "tab": format_tab,
        "zumis": format_zumis,
    }

    if fmt not in FORMAT:
        warnings.warn(
            f"Unknown format '{fmt}'. Valid formats are: {', '.join(FORMAT.keys())}"
        )
        return ""

    return FORMAT[fmt](indices, subregion_type)


def run_index(parser: ArgumentParser, args: Namespace) -> None:
    """Run the index command."""
    validate_index_args(parser, args)

    spec = load_spec(args.yaml)
    ids = args.ids.split(",") if args.ids else []

    indices = seqspec_index(
        spec,
        args.modality,
        ids,
        args.selector,
        args.rev,
    )

    # filter index for no overlap if requested
    if args.overlap:
        indices = filter_index_no_overlap(indices)

    result = format_index(indices, args.tool, args.subregion_type)

    if args.output:
        with open(args.output, "w") as f:
            print(result, file=f)
    else:
        print(result)


def filter_index_no_overlap(indices: List[Coordinate]) -> List[Coordinate]:
    # list of coordinates
    # each coordinate has an rcv, a list of region coordiantes
    # want to ensure that the intersection between all of them is empty
    rids = set()
    for idx in indices:
        new_rcv = []
        for rgn in idx.rcv:
            if rgn.region_id not in rids:
                new_rcv.append(rgn)
                rids.add(rgn.region_id)
        idx.rcv = new_rcv
    # print(indices)
    return indices


def get_index_by_files(spec: Assay, modality: str) -> List[Coordinate]:
    files = []
    for r in spec.get_seqspec(modality):
        files += r.files
    indices = get_index_by_file_ids(spec, modality, [i.file_id for i in files])
    return indices


def get_index_by_reads(spec: Assay, modality: str) -> List[Coordinate]:
    read_ids = [i.read_id for i in spec.get_seqspec(modality)]
    indices = get_index_by_read_ids(spec, modality, read_ids)
    return indices


def get_index_by_regions(spec: Assay, modality: str) -> List[Coordinate]:
    rgn = spec.get_libspec(modality)
    indices = get_index_by_region_ids(spec, modality, [rgn.region_id])
    return indices


def get_index_by_file_ids(
    spec: Assay, modality: str, file_ids: List[str]
) -> List[Coordinate]:
    # get the read associated for each file for each read get the regions by mapping primer
    files = list_files_by_file_id(spec, modality, file_ids)

    # iterate through the keys (read ids) and get the index for each read
    indices = []
    for k, v in files.items():
        index = get_coordinate_by_read_id(spec, modality, k)
        # replace query_obj with file obj. assume only one file per read
        index.query_id = v[0].file_id
        index.query_name = v[0].filename
        index.query_type = "File"
        indices.append(index)

    return indices


def get_index_by_region_ids(
    spec: Assay, modality: str, region_ids: List[str]
) -> List[Coordinate]:
    indices = []
    for id in region_ids:
        index = get_coordinate_by_region_id(spec, modality, id)
        indices.append(index)
    return indices


def get_index_by_read_ids(
    spec: Assay, modality: str, read_ids: List[str]
) -> List[Coordinate]:
    indices = []
    for id in read_ids:
        index = get_coordinate_by_read_id(spec, modality, id)
        indices.append(index)
    return indices


def get_coordinate_by_region_id(
    spec: Assay, modality: str, region_id: str
) -> Coordinate:
    regions = find_by_region_id(spec, modality, region_id)
    rgn = regions[0]

    leaves = rgn.get_leaves()
    cuts = project_regions_to_coordinates(leaves)
    coord = Coordinate(
        query_id=rgn.region_id,
        query_name=rgn.name,
        query_type="Region",
        rcv=cuts,
        strand="pos",
    )

    return coord


def get_coordinate_by_read_id(spec: Assay, modality: str, read_id: str) -> Coordinate:
    (read, rgns) = map_read_id_to_regions(spec, modality, read_id)

    # get the cuts for all of the atomic elements (tuples of 0-indexed start stop)
    rcs = project_regions_to_coordinates(rgns)

    new_rcs = itx_read(rcs, 0, read.max_len)
    coord = Coordinate(
        query_id=read.read_id,
        query_name=read.name,
        query_type="Read",
        rcv=new_rcs,
        strand=read.strand,
    )

    return coord


def format_kallisto_bus(indices: List[Coordinate], subregion_type=None):
    bcs = []
    umi = []
    feature = []
    for idx, obj in enumerate(indices):
        for cut in obj.rcv:
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


def format_kallisto_bus_force_single(indices: List[Coordinate], subregion_type=None):
    bcs = []
    umi = []
    feature = []
    longest_feature = None
    max_length = 0

    for idx, coord in enumerate(indices):
        for cut in coord.rcv:
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
                length = cut.stop - cut.start
                if length > max_length:
                    max_length = length
                    longest_feature = f"{idx},{cut.start},{cut.stop}"

    if len(umi) == 0:
        umi.append("-1,-1,-1")
    if len(bcs) == 0:
        bcs.append("-1,-1,-1")
    if longest_feature:
        feature.append(longest_feature)

    x = ",".join(bcs) + ":" + ",".join(umi) + ":" + ",".join(feature)
    return x


# this one should only return one string
# TODO: return to this
def format_seqkit_subseq(indices: List[Coordinate], subregion_type=None):
    # The x string format is start:stop (1-indexed)
    # x = ""
    # region = indices[0]
    # # need to get the right start position
    x = ""
    coord = indices[0]
    for cut in coord.rcv:
        if cut.region_type == subregion_type:
            x = f"{cut.start + 1}:{cut.stop}\n"

    return x


def format_tab(indices: List[Coordinate], subregion_type=None):
    x = ""
    for idx, coord in enumerate(indices):
        rcv = coord.rcv
        # for rgn, cuts in rcv.items():
        for cut in rcv:
            x += f"{coord.query_id}\t{cut.name}\t{cut.region_type}\t{cut.start}\t{cut.stop}\n"

    return x[:-1]


def format_starsolo(indices: List[Coordinate], subregion_type=None):
    bcs = []
    umi = []
    cdna = []
    for idx, coord in enumerate(indices):
        for cut in coord.rcv:
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


def format_simpleaf(indices: List[Coordinate], subregion_type=None):
    x = ""
    xl = []
    for idx, coord in enumerate(indices):
        fn = idx
        x = f"{fn + 1}{{"
        for cut in coord.rcv:
            if cut.region_type.upper() == "BARCODE":
                x += f"b[{cut.stop - cut.start}]"
            elif cut.region_type.upper() == "UMI":
                x += f"u[{cut.stop - cut.start}]"
            elif cut.region_type.upper() == "CDNA":
                x += f"r[{cut.stop - cut.start}]"
        x += "x:}"
        xl.append(x)
    return "".join(xl)


def format_zumis(indices: List[Coordinate], subregion_type=None):
    xl = []
    for idx, coord in enumerate(indices):
        x = ""
        for cut in coord.rcv:
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


def format_chromap(indices: List[Coordinate], subregion_type=None):
    bc_fqs = []
    bc_str = []
    gdna_fqs = []
    gdna_str = []
    for idx, coord in enumerate(indices):
        strand = "" if coord.strand == "pos" else ":-"
        for cut in coord.rcv:
            if cut.region_type.upper() == "BARCODE":
                bc_fqs.append(coord.query_id)
                bc_str.append(f"bc:{cut.start}:{cut.stop - 1}{strand}")
                pass
            elif cut.region_type.upper() == "GDNA":
                gdna_fqs.append(coord.query_id)
                gdna_str.append(f"{cut.start}:{cut.stop - 1}")
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
            d.append(RegionCoordinateDifference(obj=rgnc1, fixed=rgnc2, rgncdiff=diff))

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


def format_relative(indices: List[Coordinate], subregion_type=None):
    x = ""
    for idx, coord in enumerate(indices):
        rg_strand = coord.strand  # noqa
        # compute differences across all region coordinates for this coordinate
        diffs = compute_relative(coord.rcv)
        filtered = filter_differences(diffs)
        filtered.sort(key=lambda diff: diff.obj.region_type)

        for diff in filtered:
            x += (
                f"{diff.obj.region_id}\t{diff.fixed.region_id}\t"
                f"{diff.rgncdiff.start}\t{diff.rgncdiff.stop}\t{diff.loc}\n"
            )
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


def format_splitcode(indices: List[Coordinate], subregion_type=None):
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
    for idx, coord in enumerate(indices):
        # compute differences across all region coordinates for this coordinate
        d = compute_relative(coord.rcv)

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

    for idx, coord in enumerate(indices):
        # rg_strand = region.pop("strand")  # noqa
        lc = ""
        x += "groups\tids\ttags\tdistances\tlocations\n"
        idx = 1
        for cut in coord.rcv:
            lc += f"{cut.name}[{cut.min_len}]\t{cut.sequence}\n"
            if cut.region_type == "linker":
                # forward, regular and complement
                x += f"group{idx}\t{cut.name}f\t{cut.sequence}\t3:3:3\t0:0:0\n"
                x += f"group{idx}\t{cut.name}c\t{complement_sequence(cut.sequence)}\t3:3:3\t0:0:0\n"

                # reverse, regular and complement
                x += f"group{idx}\t{cut.name}r\t{cut.sequence[::-1]}\t3:3:3\t0:0:0\n"
                x += f"group{idx}\t{cut.name}rc\t{complement_sequence(cut.sequence)[::-1]}\t3:3:3\t0:0:0\n"
                idx += 1
    return x

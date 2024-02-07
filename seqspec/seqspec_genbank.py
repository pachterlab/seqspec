from seqspec.utils import load_genbank
import json
from seqspec.Region import Region
from seqspec.Assay import Assay


def setup_genbank_args(parser):
    subparser = parser.add_parser(
        "genbank",
        description="get genbank about seqspec file",
        help="get genbank about seqspec file",
    )

    subparser.add_argument("gbk", help="Genbank file")
    subparser.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
        required=False,
    )
    return subparser


def validate_genbank_args(parser, args):
    # if everything is valid the run_genbank
    fn = args.gbk
    o = args.o
    gb = load_genbank(fn)

    spec = run_genbank(gb)

    if o:
        spec.to_YAML(o)
    else:
        print(json.dumps(spec, sort_keys=False, indent=4))


def run_genbank(gb):
    ex = gb_to_list(gb)
    nested_json = nest_intervals(ex)
    filled_regions = fill_gaps(gb.sequence, nested_json)
    regions = convert(filled_regions)
    spec = Assay(
        "genbank",
        "illumina",
        "genbank thing",
        "doi",
        "date",
        "description",
        ["source"],
        "",
        regions,
    )
    return spec


def gb_to_list(gb):
    feat = []
    label = "source"
    for f in gb.features:
        id = f.key

        if "complement" in f.location:
            start, stop = tuple(map(int, f.location[11:-1].split("..")))
        else:
            start, stop = tuple(map(int, f.location.split("..")))

        # convert to 0-index
        start -= 1
        length = stop - start
        seq = gb.sequence[start:stop]

        for q in f.qualifiers:
            if q.key == "/label=":
                label = q.value
                break
        feat.append(
            {
                "id": id,
                "label": label,
                "start": start,
                "stop": stop,
                "length": length,
                "seq": seq,
            }
        )
    return feat


def nest_intervals(intervals):
    def nest(start_index, end_limit):
        nested = []

        i = start_index
        while i < len(intervals) and intervals[i]["start"] < end_limit:
            current_interval = intervals[i]
            child, next_index = nest(i + 1, current_interval["stop"])
            interval_obj = {
                "id": current_interval["id"],
                "label": current_interval["label"],
                "start": current_interval["start"],
                "stop": current_interval["stop"],
                "length": current_interval["length"],
                "seq": current_interval["seq"],
                "regions": child,
            }
            nested.append(interval_obj)
            i = next_index

        return nested, i

    result, _ = nest(0, intervals[0]["stop"])
    return result


def fill_gaps(seq, regions, parent_start=0, parent_stop=0):
    if len(regions) == 0:
        return []

    # Insert a filler at the start if necessary
    if regions[0]["start"] > parent_start:
        start = parent_start
        stop = regions[0]["start"]
        s = seq[start:stop]
        regions.insert(
            0,
            {
                "id": "filler_start",
                "label": "filler_start",
                "start": start,
                "stop": stop,
                "length": stop - start,
                "seq": s,
                "regions": [],
            },
        )

    new_regions = []
    for i, region in enumerate(regions):
        # Append the current region
        new_regions.append(region)

        # Recursive call for nested regions
        if "regions" in region:
            region["regions"] = fill_gaps(
                seq, region["regions"], region["start"], region["stop"]
            )

        # Check for gap and insert a filler
        if i < len(regions) - 1 and region["stop"] < regions[i + 1]["start"]:
            filler_id = f'filler_{region["id"]}_{regions[i+1]["id"]}'
            start = region["stop"]
            stop = regions[i + 1]["start"]
            s = seq[start:stop]
            new_regions.append(
                {
                    "id": filler_id,
                    "label": filler_id,
                    "start": start,
                    "stop": stop,
                    "length": stop - start,
                    "seq": s,
                    "regions": [],
                }
            )

    # Insert a filler at the end if necessary
    if new_regions[-1]["stop"] < parent_stop:
        start = new_regions[-1]["stop"]
        stop = parent_stop
        s = seq[start:stop]
        new_regions.append(
            {
                "id": "filler_end",
                "label": "filler_end",
                "start": start,
                "stop": stop,
                "length": stop - start,
                "seq": s,
                "regions": [],
            }
        )

    return new_regions


# convert filled regions to seqspec, must be recursive function
# regions is a list
def convert(regions):
    if len(regions) == 0:
        return []
    new_regions = []
    for r in regions:
        rgn = Region(
            r["id"],
            "",
            r["label"],
            "fixed",
            r["seq"],
            r["length"],
            r["length"],
            None,
            None,
        )
        if len(r["regions"]) > 0:
            rgn.regions = convert(r["regions"])
        new_regions.append(rgn)
    return new_regions

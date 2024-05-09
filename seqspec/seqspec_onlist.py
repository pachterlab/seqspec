from seqspec.Assay import Assay
from seqspec.Region import project_regions_to_coordinates, itx_read, Onlist
from seqspec.utils import load_spec, map_read_id_to_regions
from seqspec.seqspec_find import run_find_by_type, run_find
import os
from seqspec.utils import read_local_list, read_remote_list
import itertools
from typing import List


def setup_onlist_args(parser):
    subparser = parser.add_parser(
        "onlist",
        description="get onlist file for specific region",
        help="get onlist file for specific regions",
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
    format_choices = ["read", "region", "region-type"]
    subparser.add_argument(
        "-s",
        metavar="SPECOBJECT",
        type=str,
        default="read",
        choices=format_choices,
        help=f"Type of spec object ({', '.join(format_choices)}), default: region",
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
        "-r",
        metavar="READ or REGION",
        help=("Read or Region"),
        type=str,
        default=None,
        required=False,
    )
    format_choices = ["product", "multi"]
    subparser.add_argument(
        "-f",
        metavar="FORMAT",
        type=str,
        default="product",
        choices=format_choices,
        help=f"Format for combining multiple onlists ({', '.join(format_choices)}), default: product",
    )
    subparser.add_argument("--list", action="store_true", help=("List onlists"))
    return subparser


def validate_onlist_args(parser, args):
    # get paramters
    fn = args.yaml
    m = args.m
    r = args.r
    f = args.f

    # the base path is the path to the spec file
    base_path = os.path.dirname(os.path.abspath(fn))

    # set the save path if it exists
    if args.o:
        save_path = os.path.abspath(args.o)
    else:
        # otherwise the save path is the same path as the spec
        save_path = os.path.join(base_path, "onlist_joined.txt")

    # load spec
    spec = load_spec(fn)
    # if number of barcodes > 1 then we need to join them
    # note that in order to enable --list as an option we make regions optional but its
    # required for the standard onlist function
    if args.list:
        onlists = run_list_onlists(spec, m)
        for ol in onlists:
            print(f"{ol['region_id']}\t{ol['filename']}\t{ol['location']}\t{ol['md5']}")
        return

    CMD = {
        "region": run_onlist_region,
        "region-type": run_onlist_region_type,
        "read": run_onlist_read,
    }
    if args.s in CMD.keys():
        onlists = CMD[args.s](spec, m, r)
    else:
        raise ValueError(f"Unrecognized spec object {args.s}")

    if len(onlists) == 0:
        raise ValueError(f"No onlist found for {m}, {args.s}, {r}")

    # for only one onlist we can just return the path
    # if only one, its remote and we save it to the base path
    elif len(onlists) == 1:
        location = onlists[0].location
        onlist_fn = os.path.basename(onlists[0].filename)
        onlist_path = os.path.join(base_path, onlist_fn)

        if os.path.exists(onlist_path):
            location = "local"
        elif location == "remote":
            # download the onlist to the base path and return the path
            onlist_elements = read_remote_list(onlists[0])
            onlist_path = write_onlist(onlist_elements, save_path)

    # anytime we join onlists, we create a new onlist file
    elif len(onlists) > 1:
        lsts = []
        for o in onlists:
            if o.location == "local":
                lsts.append(read_local_list(o, base_path))
            elif o.location == "remote":
                # base_path is ignored for remote onlists
                lsts.append(read_remote_list(o, base_path))
        onlist_elements = join_onlists(lsts, f)
        onlist_path = write_onlist(onlist_elements, save_path)

    # print the path to the onlist
    print(onlist_path)
    return onlist_path


def run_onlist_region_type(
    spec: Assay, modality: str, region_type: str
) -> List[Onlist]:
    regions = run_find_by_type(spec, modality, region_type)
    onlists: List[Onlist] = []
    for r in regions:
        ol = r.get_onlist()
        if ol:
            onlists.append(ol)
    return onlists


def run_onlist_region(spec: Assay, modality: str, region_id: str) -> List[Onlist]:
    regions = run_find(spec, modality, region_id)
    onlists: List[Onlist] = []
    for r in regions:
        onlists.append(r.get_onlist())
    if len(onlists) == 0:
        raise ValueError(f"No onlist found for region {region_id}")
    return onlists


def run_onlist_read(spec: Assay, modality: str, read_id: str) -> List[Onlist]:
    (read, rgns) = map_read_id_to_regions(spec, modality, read_id)
    # convert regions to region coordinates
    rcs = project_regions_to_coordinates(rgns)
    # intersect read with region coordinates
    new_rcs = itx_read(rcs, 0, read.max_len)

    onlists: List[Onlist] = []
    for r in new_rcs:
        ol = r.get_onlist()
        if ol:
            onlists.append(ol)

    return onlists


def run_list_onlists(spec: Assay, modality: str):
    regions = spec.get_libspec(modality).get_onlist_regions()
    olsts = []
    for r in regions:
        if r.onlist is None:
            continue
        olsts.append(
            {
                "region_id": r.region_id,
                "filename": r.onlist.filename,
                "location": r.onlist.location,
                "md5": r.onlist.md5,
            }
        )
    return olsts


def find_list_target_dir(onlists):
    for olst in onlists:
        if olst.location == "local":
            base_path = os.path.dirname(os.path.abspath(onlists[0].filename))
            if os.access(base_path, os.W_OK):
                return base_path

    return os.getcwd()


def join_onlists(onlists: List[List[str]], fmt: str) -> List[str]:
    """Given a list of onlist objects return a file containing the combined list"""

    # base path should be the path relative to the spec file
    # join the onlists
    formatter_functions = {
        "product": join_product_onlist,
        "multi": join_multi_onlist,
    }
    joined_onlist = list(formatter_functions[fmt](onlists))

    return joined_onlist


def write_onlist(onlist: List[str], path: str) -> str:
    with open(path, "w") as f:
        for line in onlist:
            f.write(f"{line}\n")
    return path


def join_product_onlist(lsts: List[List[str]]):
    for i in itertools.product(*lsts):
        yield f"{''.join(i)}"


def join_multi_onlist(lsts: List[List[str]]):
    for row in itertools.zip_longest(*lsts, fillvalue="-"):
        yield f"{' '.join((str(x) for x in row))}"

from seqspec.Assay import Assay
from seqspec.Region import project_regions_to_coordinates, itx_read
from seqspec.utils import load_spec, map_read_id_to_regions
from seqspec.seqspec_find import run_find_by_type
import os
from seqspec.utils import read_list
import itertools


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
    subparser.add_argument(
        "--region",
        help="Specify a region",
        action="store_true",
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
    subparser.add_argument(
        "-f",
        metavar="FORMAT",
        type=str,
        default="product",
        choices=["product", "multi"],
        help="select between cartesian product 'product' or multiple barcode lists in file 'multi'"
    )
    subparser.add_argument("--list", action="store_true", help=("List onlists"))
    return subparser


def validate_onlist_args(parser, args):
    # get paramters
    fn = args.yaml
    m = args.m
    r = args.r
    f = args.f
    # TODO: if onlist is a link, download. also fix output path
    # o = args.o
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
    if args.region:
        olist = run_onlist_region(spec, m, r, f)
    else:
        olist = run_onlist_read(spec, m, r, f)
    print(os.path.join(os.path.dirname(os.path.abspath(fn)), olist))
    return


def run_onlist_region(spec: Assay, modality: str, region_id: str, fmt: str):
    # for now return the path to the onlist file for the modality/region pair

    # run function
    regions = run_find_by_type(spec, modality, region_id)
    onlists = []
    for r in regions:
        onlists.append(r.get_onlist().filename)
    if len(onlists) == 0:
        raise ValueError(f"No onlist found for region {region_id}")
    return join_onlists(onlists, fmt)


def run_onlist_read(spec: Assay, modality: str, read_id: str, fmt: str):
    # for now return the path to the onlist file for the modality/region pair

    # run function
    (read, rgns) = map_read_id_to_regions(spec, modality, read_id)
    # convert regions to region coordinates
    rcs = project_regions_to_coordinates(rgns)
    # intersect read with region coordinates
    new_rcs = itx_read(rcs, 0, read.max_len)

    onlists = []
    for r in new_rcs:
        ol = r.get_onlist()
        if ol:
            onlists.append(ol.filename)

    if len(onlists) == 0:
        raise ValueError(f"No onlist found for read {read_id}")

    return join_onlists(onlists, fmt)


def run_list_onlists(spec: Assay, modality: str):
    regions = spec.get_libspec(modality).get_onlist_regions()
    olsts = []
    for r in regions:
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
    for l in onlists:
        if l.location == "local":
            base_path = os.path.dirname(os.path.abspath(onlists[0].filename))
            if os.access(base_path, os.W_OK):
                return base_path

    return os.getcwd()


def join_onlists(onlists, fmt):
    """Given a list of onlist objects return a file containing the combined list
    """
    if len(onlists) == 0:
        print("No lists present")
        return
    elif len(onlists) == 1 and onlists[0].location.lower() == "local":
        return onlists[0].filename
    else:
        base_path = find_list_target_dir(onlists)
        # join the onlists
        lsts = [read_list(o) for o in onlists]
        joined_path = os.path.join(base_path, "onlist_joined.txt")
        formatter_functions = {
            "product": join_product_onlist,
            "multi": join_multi_onlist,
        }
        formatter = formatter_functions.get(fmt)
        if formatter is None:
            raise ValueError("Unrecognized format type {}. Expected".format(
                fmt, list(formatter_functions.keys())))

        with open(joined_path, "w") as f:
            for line in formatter(lsts):
                f.write(line)

        return joined_path


def join_product_onlist(lsts):
    for i in itertools.product(*lsts):
        yield f"{''.join(i)}\n"


def join_multi_onlist(lsts):
    for row in itertools.zip_longest(*lsts, fillvalue='-'):
        yield f"{' '.join((str(x) for x in row))}\n"

from seqspec.utils import load_spec
from seqspec.Assay import Assay
from collections import defaultdict
from seqspec.File import File
from typing import Dict, List, Optional


def setup_file_args(parser):
    subparser = parser.add_parser(
        "file",
        description="list files",
        help="list files",
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
        "-i",
        metavar="IDs",
        help=("Ids to list"),
        type=str,
        default=None,
    )
    subparser_required.add_argument(
        "-m",
        metavar="MODALITY",
        help=("Modality"),
        type=str,
        default=None,
        required=True,
    )
    # the object we are using to index
    choices = ["read", "region", "file", "onlist"]
    subparser.add_argument(
        "-s",
        metavar="SELECTOR",
        help=(f"Selector for ID, [{', '.join(choices)}] (default: read)"),
        type=str,
        default="read",
        choices=choices,
    )
    choices = ["paired", "interleaved", "index", "list"]
    subparser.add_argument(
        "-f",
        metavar="FORMAT",
        help=f"Format, [{', '.join(choices)}], default: paired",
        type=str,
        default="paired",
        choices=choices,
    )
    choices = [
        "file_id",
        "filename",
        "filetype",
        "filesize",
        "url",
        "urltype",
        "md5",
        "all",
    ]
    subparser.add_argument(
        "-k",
        metavar="KEY",
        help=f"Key, [{', '.join(choices)}], default: file_id",
        type=str,
        default="file_id",
        choices=choices,
    )

    return subparser


def validate_file_args(parser, args):
    spec_fn = args.yaml
    o = args.o
    m = args.m  # modality
    idtype = args.s  # selector
    fmt = args.f  # format
    ids = args.i  # ids
    k = args.k  # key

    if (k == "filesize" or k == "filetype" or k == "urltype" or k == "md5") and (
        fmt == "paired" or fmt == "interleaved" or fmt == "index"
    ):
        parser.error(f"-f {fmt} valid only with -k file_id, filename, url")

    return run_file(spec_fn, m, ids, idtype, fmt, k, o)


def run_file(spec_fn, m, ids, idtype, fmt, k, o):
    spec = load_spec(spec_fn)
    if ids is None:
        ids = []
    else:
        ids = ids.split(",")
    files = file(spec, m, ids, idtype, fmt, k)

    if files:
        if o:
            with open(o, "w") as f:
                print(files, file=f)
        else:
            print(files)
    return


def file(
    spec: Assay,
    modality: str,
    ids: List[str],
    idtype: str,
    fmt: str,
    k: Optional[str],
):
    # NOTE: LIST FILES DOES NOT RESPECT ORDERING OF INPUT IDs LIST
    LIST_FILES = {
        "read": list_read_files,
        "region": list_region_files,
        "file": list_files,
        "onlist": list_onlist_files,
    }
    LIST_FILES_BY_ID = {
        "read": list_files_by_read_id,
        "file": list_files_by_file_id,
    }
    if len(ids) == 0:
        # list all the files
        files = LIST_FILES[idtype](spec, modality)
    else:
        # list only the id files
        files = LIST_FILES_BY_ID[idtype](spec, modality, ids)

    FORMAT = {
        "list": format_list_files_metadata,
        "paired": format_list_files,
        "interleaved": format_list_files,
        "index": format_list_files,
    }

    x = FORMAT[fmt](files, fmt, k)
    return x


def list_read_files(spec, modality):
    files = defaultdict(list)
    reads = spec.get_seqspec(modality)
    for rd in reads:
        files[rd.read_id] = rd.files
    return files


def list_files(spec, modality):
    files_rd = list_read_files(spec, modality)
    files_rgn = list_region_files(spec, modality)
    return {**files_rd, **files_rgn}


def list_onlist_files(spec, modality):
    files = defaultdict(list)
    regions = spec.get_libspec(modality).get_onlist_regions()
    for r in regions:
        if r.onlist is None:
            continue
        files[r.region_id].append(r.onlist)
    return files


def list_region_files(spec, modality):
    return list_onlist_files(spec, modality)


def format_list_files_metadata(files: Dict[str, List[File]], fmt, k):
    x = ""
    if k == "all":
        for items in zip(*files.values()):
            for key, item in zip(files.keys(), items):
                x += f"{key}\t{item.file_id}\t{item.filename}\t{item.filetype}\t{item.filesize}\t{item.url}\t{item.urltype}\t{item.md5}\n"
        x = x[:-1]

    else:
        for items in zip(*files.values()):
            for key, item in zip(files.keys(), items):
                attr = str(getattr(item, k))
                id = item.file_id
                x += f"{key}\t{id}\t{attr}\n"
        x = x[:-1]

    return x


def format_list_files(files: Dict[str, List[File]], fmt, k=None):
    x = ""
    if fmt == "paired":
        for items in zip(*files.values()):
            if k:
                x += "\t".join([str(getattr(i, k)) for i in items]) + "\n"
            else:
                x += "\t".join([i.filename for i in items]) + "\n"
        x = x[:-1]

    elif fmt == "interleaved" or fmt == "list":
        for items in zip(*files.values()):
            for item in items:
                id = item.filename
                if k:
                    id = str(getattr(item, k))
                x += id + "\n"
        x = x[:-1]
    elif fmt == "index":
        for items in zip(*files.values()):
            for item in items:
                id = item.filename
                if k:
                    id = str(getattr(item, k))
                x += id + ","
        x = x[:-1]

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
                # files[read.read_id].append(file.filename)
                files[read.read_id].append(file)
    return files


def list_files_by_file_id(spec, modality, file_ids):
    seqspec = spec.get_seqspec(modality)
    ids = set(file_ids)
    files = defaultdict(list)
    # TODO: NOTE ORDERING HERE IS IMPORTANT SEE RUN_LIST_FILES FUNCTION
    for read in seqspec:
        for file in read.files:
            if file.filename in ids:
                # files[read.read_id].append(file.filename)
                files[read.read_id].append(file)
    return files

from seqspec.utils import load_spec
from seqspec.Assay import Assay
from collections import defaultdict
from seqspec.File import File
from typing import Dict, List, Optional
from argparse import RawTextHelpFormatter
import json
from seqspec import seqspec_find
import os
import argparse


def setup_file_args(parser):
    subparser = parser.add_parser(
        "file",
        description="""
List files present in seqspec file.

Examples:
seqspec file -m rna spec.yaml                                          # List paired read files
seqspec file -m rna -f interleaved spec.yaml                           # List interleaved read files
seqspec file -m rna -f list -k url spec.yaml                           # List urls of all read files
seqspec file -m rna -f list -s region -k all spec.yaml                 # List all files in regions
seqspec file -m rna -f json -s region-type -k all -i barcode spec.yaml # List files for barcode regions in json
---
""",
        help="List files present in seqspec file",
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
    # choices = ["read", "region", "file", "onlist", "region-type"]
    choices = ["read", "region", "file", "region-type"]
    subparser.add_argument(
        "-s",
        metavar="SELECTOR",
        help=(f"Selector for ID, [{', '.join(choices)}] (default: read)"),
        type=str,
        default="read",
        choices=choices,
    )
    choices = ["paired", "interleaved", "index", "list", "json"]
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

    # option to get the full path of the file
    subparser.add_argument(
        "--fullpath",
        help=argparse.SUPPRESS,
        action="store_true",
        default=False,
    )

    return subparser


def validate_file_args(parser, args):
    spec_fn = os.path.abspath(args.yaml)
    o = args.o
    m = args.m  # modality
    idtype = args.s  # selector
    fmt = args.f  # format
    ids = args.i  # ids
    k = args.k  # key
    fp = args.fullpath

    if (k == "filesize" or k == "filetype" or k == "urltype" or k == "md5") and (
        fmt == "paired" or fmt == "interleaved" or fmt == "index"
    ):
        parser.error(f"-f {fmt} valid only with -k file_id, filename, url")

    return run_file(spec_fn, m, ids, idtype, fmt, k, o, fp=fp)


def run_file(spec_fn, m, ids, idtype, fmt, k, o, fp=False):
    spec = load_spec(spec_fn)
    if ids is None:
        ids = []
    else:
        ids = ids.split(",")
    files = file(spec, m, ids, idtype, fmt, k, spec_fn, fp)

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
    spec_fn: str,
    fp: bool = False,
):
    # NOTE: LIST FILES DOES NOT RESPECT ORDERING OF INPUT IDs LIST
    # NOTE: seqspec file -s read gets the files for the read, not the files mapped from the regions associated with the read.
    LIST_FILES = {
        "read": list_read_files,
        "region": list_region_files,
        "file": list_files,
        # "onlist": list_onlist_files,
    }
    LIST_FILES_BY_ID = {
        "read": list_files_by_read_id,
        "file": list_files_by_file_id,
        "region": list_files_by_region_id,
        "region-type": list_files_by_region_type,
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
        "json": format_json_files,
    }

    x = FORMAT[fmt](files, fmt, k, spec_fn, fp)
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


def format_list_files_metadata(
    files: Dict[str, List[File]], fmt, k, spec_fn="", fp=False
):
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


def format_json_files(files: Dict[str, List[File]], fmt, k, spec_fn="", fp=False):
    x = []
    for items in zip(*files.values()):
        if k == "all":
            for key, item in zip(files.keys(), items):
                d = item.to_dict()
                if item.urltype == "local" and fp:
                    d["url"] = os.path.join(os.path.dirname(spec_fn), d["url"])
                x.append(d)
        else:
            for key, item in zip(files.keys(), items):
                attr = getattr(item, k)
                if k == "url" and item.urltype == "local" and fp:
                    attr = os.path.join(os.path.dirname(spec_fn), attr)
                x.append({"file_id": item.file_id, k: attr})
    return json.dumps(x, indent=4)


def format_list_files(files: Dict[str, List[File]], fmt, k=None, spec_fn="", fp=False):
    x = ""
    if fmt == "paired":
        x = ""
        for items in zip(*files.values()):
            t = ""
            for i in items:
                if k:
                    attr = str(getattr(i, k))
                    if k == "url" and i.urltype == "local" and fp:
                        attr = os.path.join(os.path.dirname(spec_fn), attr)
                    t += f"{attr}\t"
                else:
                    t += f"{i.filename}\t"
            x += f"{t[:-1]}\n"
        x = x[:-1]

    elif fmt == "interleaved" or fmt == "list":
        for items in zip(*files.values()):
            for item in items:
                id = item.filename
                if k:
                    id = str(getattr(item, k))
                    if k == "url" and item.urltype == "local" and fp:
                        id = os.path.join(os.path.dirname(spec_fn), id)
                x += id + "\n"
        x = x[:-1]
    elif fmt == "index":
        for items in zip(*files.values()):
            for item in items:
                id = item.filename
                if k:
                    id = str(getattr(item, k))
                    if k == "url" and item.urltype == "local" and fp:
                        id = os.path.join(os.path.dirname(spec_fn), id)
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


def list_files_by_region_id(spec, modality, file_ids):
    files = list_region_files(spec, modality)

    ids = set(file_ids)
    new_files = defaultdict(list)
    for region_id, files in files.items():
        if region_id in ids:
            new_files[region_id] += files
    return new_files


def list_files_by_region_type(spec, modality, file_ids):
    files = list_region_files(spec, modality)

    ids = set(file_ids)
    new_files = defaultdict(list)
    for region_id, files in files.items():
        r = seqspec_find.find_by_region_id(spec, modality, region_id)[0]
        rt = r.region_type
        if rt in ids:
            new_files[region_id] += files
    return new_files

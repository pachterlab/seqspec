import gzip
import io
import os
import re
from pathlib import Path
from typing import IO, List, Optional, Tuple, Union

import requests
import yaml
from Bio import GenBank
from pydantic import ValidationError

from seqspec.Assay import Assay
from seqspec.File import File
from seqspec.Read import Read
from seqspec.Region import Onlist, Region

# def strip_yaml_tags(yaml_str: str) -> str:
#     """
#     Removes leading YAML tags like !Assay or !Read from the input string.
#     """
#     return re.sub(r'^ *!(\w+)', '', yaml_str, flags=re.MULTILINE)


# def safe_load_strip_tags(stream: Union[str, IO, Path]):
#     """
#     Reads a YAML string or file-like object, strips YAML tags,
#     and safely loads it using yaml.safe_load().
#     """
#     if isinstance(stream, (str, Path)):
#         with open(stream, "r") as f:
#             raw = f.read()
#     else:
#         raw = stream.read()

#     cleaned = strip_yaml_tags(raw)
#     return yaml.safe_load(cleaned)

# def load_spec(spec_fn: str):
#     try:
#         with gzip.open(spec_fn, "rt") as stream:
#             return load_spec_stream(stream)
#     except gzip.BadGzipFile:
#         with open(spec_fn, "r") as stream:
#             return load_spec_stream(stream)


# def load_spec_stream(spec_stream: IO):
#     data_dict = safe_load_strip_tags(spec_stream)
#     assay = Assay(**data_dict)

#     for r in assay.library_spec:
#         r.set_parent_id(None)

#     return assay


# --- Known tags to strip from the YAML ---
KNOWN_TAGS = [
    "!Assay",
    "!File",
    "!LibProtocol",
    "!LibKit",
    "!SeqProtocol",
    "!SeqKit",
    "!Read",
    "!Onlist",
    "!Region",
]

# Regex pattern to match known tags in all common positions
TAG_PATTERN = re.compile(
    r"""(?x)  # verbose mode
    (^|\s|:)      # start of line, whitespace, or mapping colon
    ("""
    + "|".join(re.escape(tag) for tag in KNOWN_TAGS)
    + r""")
    (?=\s|$|[:\[\]{},])  # followed by space, end of line, or YAML structure characters
    """
)


def strip_yaml_tags(yaml_str: str) -> str:
    """
    Removes known YAML tags from anywhere in the input YAML text.
    """
    return TAG_PATTERN.sub(r"\1", yaml_str)


def safe_load_strip_tags(stream: Union[str, Path, IO]) -> dict:
    """
    Reads a YAML string or file-like object, strips known YAML tags,
    and safely loads it using yaml.safe_load().
    """
    if isinstance(stream, (str, Path)):
        with open(stream, "r") as f:
            raw = f.read()
    else:
        raw = stream.read()

    cleaned = strip_yaml_tags(raw)
    return yaml.safe_load(cleaned)


def format_pydantic_validation_object(error_path: str) -> str:
    """
    Converts a Pydantic validation error path to Python dictionary access notation.

    Args:
        error_path: Path like 'library_spec.0.regions.1.onlist.url'

    Returns:
        Python dictionary access notation like "spec['library_spec'][0]['regions'][1]['onlist']['url']"
    """
    if not error_path:
        return "spec"

    parts = error_path.split(".")
    result = "spec"

    for part in parts:
        # Check if part is a number (array index)
        if part.isdigit():
            result += f"[{part}]"
        else:
            result += f"['{part}']"

    return result


def load_spec(spec_fn: Union[str, Path], strict=True) -> Assay:
    """
    Loads a YAML or gzipped YAML spec file, strips tags, and constructs an Assay object.
    If strict=True and validation fails, prints all errors and raises an exception.
    """
    # Check if the file is gzip by reading the magic number
    with open(spec_fn, "rb") as f:
        magic = f.read(2)

    if magic == b"\x1f\x8b":
        with gzip.open(spec_fn, "rt") as stream:
            data_dict = safe_load_strip_tags(stream)
    else:
        with open(spec_fn, "r") as stream:
            data_dict = safe_load_strip_tags(stream)

    if strict:
        try:
            assay = Assay(**data_dict)
            return assay
        except ValidationError as e:
            verrors = e.errors()
            errors = []
            for idx, err in enumerate(verrors, 1):
                # err['loc'] is a tuple of the error path, join with dots for readability
                err_path = ".".join(str(x) for x in err.get("loc", []))
                err_type = err.get("type", "unknown")
                err_msg = err.get("msg", "")
                # Compose a descriptive error message
                errors.append(
                    {
                        "error_type": err_type,
                        "error_message": err_msg,
                        "error_object": format_pydantic_validation_object(err_path),
                        "full_error": err,
                    }
                )

            for idx, error in enumerate(errors, 1):
                print(
                    f"[error {idx}] {error['error_message']} in {error['error_object']}"
                )
            raise ValueError(
                "Invalid spec. Correct errors then verify spec with `seqspec format` and `seqspec check`."
            )
    else:
        from seqspec.Assay import AssayInput

        return AssayInput(**data_dict).to_assay()


def load_spec_stream(spec_stream: IO) -> Assay:
    """
    Parses a YAML stream, strips tags, and returns a validated Assay object.
    """
    data_dict = safe_load_strip_tags(spec_stream)
    from seqspec.Assay import AssayInput

    assay = AssayInput(**data_dict).to_assay()
    return assay


def yaml_safe_dump(obj):
    if isinstance(obj, list):
        return [o.model_dump() if hasattr(o, "model_dump") else o for o in obj]
    elif hasattr(obj, "model_dump"):
        return obj.model_dump()
    else:
        return obj


def load_genbank(gbk_fn: str):
    with open(gbk_fn, "r") as stream:
        return load_genbank_stream(stream)


def load_genbank_stream(gbk_stream: io.IOBase):
    data: GenBank = GenBank.read(gbk_stream)  # type: ignore
    return data


def write_read(header, seq, qual, f):
    f.write(f"{header}\n{seq}\n+\n{qual}\n")


def write_pydantic_to_file_or_stdout(
    resource: Union[
        Read, File, Region, Assay, List[Read], List[File], List[Region], Assay
    ],
    output: Optional[Path],
) -> None:
    """Write spec to file or stdout."""
    dump = yaml_safe_dump(resource)

    # Handle output
    if output:
        with open(output, "w") as f:
            yaml.dump(dump, f, sort_keys=False)
    else:
        print(yaml.dump(dump, sort_keys=False))


def yield_onlist_contents(stream):
    for line in stream:
        yield line.strip().split()[0]


def read_local_list(onlist: Onlist, base_path: str = "") -> List[str]:
    filename = os.path.join(base_path, onlist.filename)
    stream = open(filename, "rb")
    # do we need to decompress?
    if filename.endswith(".gz"):
        stream = gzip.GzipFile(fileobj=stream)

    # convert to text stream
    stream = io.TextIOWrapper(stream)

    results = []
    for i in yield_onlist_contents(stream):
        results.append(i)
    stream.close()
    return results


def read_remote_list(onlist: Onlist, base_path: str = "") -> List[str]:
    """Given an onlist object read the local or remote data"""
    filename = str(onlist.filename)
    if onlist.url:
        filename = str(onlist.url)

    stream = None
    try:
        # open stream
        auth = get_remote_auth_token()
        response = requests.get(filename, stream=True, auth=auth)
        response.raise_for_status()
        stream = response.raw

        # do we need to decompress?
        if filename.endswith(".gz"):
            stream = gzip.GzipFile(fileobj=stream)

        # convert to text stream
        stream = io.TextIOWrapper(stream)

        results = []
        for i in yield_onlist_contents(stream):
            # add the new line when writing to file
            results.append(i)
    finally:
        if stream is None:
            print("Warning: unable to open barcode file {}".format(filename))
        else:
            stream.close()

    return results


def get_remote_auth_token():
    """Look for authentication tokens for accessing remote resources"""
    username = os.environ.get("IGVF_API_KEY")
    password = os.environ.get("IGVF_SECRET_KEY")
    if not (username is None or password is None):
        auth = (username, password)
    else:
        auth = None

    return auth


def region_ids_in_spec(seqspec, modality, region_ids):
    # return True if all region_ids are in seqspec
    spec = seqspec.get_libspec(modality)
    found = []
    for region_id in region_ids:
        found += [r.region_id for r in spec.get_region_by_id(region_id)]
    return found


def file_exists(uri):
    try:
        if uri.startswith("https://api.data.igvf.org"):
            auth = get_remote_auth_token()
            if auth is None:
                print("Warning: IGVF_API_KEY and IGVF_SECRET_KEY not set")
            r = requests.head(uri, auth=auth)
            if r.status_code == 307:
                # igvf download link will redirect to a presigned amazon s3 url, HEAD request will not work.
                r = requests.get(r.headers["Location"], headers={"Range": "bytes=0-0"})
                return r.status_code == 206
            return r.status_code == 200
        r = requests.head(uri)
        if r.status_code == 302:
            return file_exists(r.headers["Location"])
        return r.status_code == 200
    except requests.ConnectionError:
        return False


REGION_TYPE_COLORS = {
    "barcode": "#2980B9",
    "cdna": "#8E44AD",
    "custom_primer": "#3CB371",
    "fastq": "#F1C40F",
    "gdna": "#E67E22",
    "illumina_p5": "#E17A47",
    "illumina_p7": "#E17A47",
    "index5": "#4AB19D",
    "index7": "#4AB19D",
    "linker": "#1ABC9C",
    "me1": "#E74C3C",
    "me2": "#E74C3C",
    "nextera_read1": "#FF8000",
    "nextera_read2": "#FF8000",
    "poly_a": "#FF0000",
    "poly_g": "#C0C0C0",
    "poly_t": "#7F8C8D",
    "poly_c": "#2C3E50",
    "s5": "#EF3D59",
    "s7": "#EF3D59",
    "truseq_read1": "#EFC958",
    "truseq_read2": "#EFC958",
    "umi": "#16A085",
    "tag": "#344E5C",
    "protein": "#ECF0F1",
    "named": "#FF8C00",
}

# unused

# '#95A5A6'


def map_read_id_to_regions(
    spec: Assay, modality: str, read_id: str
) -> Tuple[Read, List[Region]]:
    # get the read object and primer id
    read = spec.get_read(read_id)
    primer_id = read.primer_id

    # get all atomic elements from library
    libspec = spec.get_libspec(modality)

    # get the (ordered) leaves ensuring region with primer_id is included (but not its children)
    leaves = libspec.get_leaves_with_region_id(primer_id)
    # print(leaves)
    # get the index of the primer in the list of leaves (ASSUMPTION, 5'->3' and primer can be any node)
    pidxs = [idx for idx, leaf in enumerate(leaves) if leaf.region_id == primer_id]
    if len(pidxs) == 0:
        raise IndexError(
            "primer_id {} not found in regions {}".format(
                primer_id, [leaf.region_id for leaf in leaves]
            )
        )
    primer_idx = pidxs[0]

    # If we are on the opposite strand, we go in the opposite way
    if read.strand == "neg":
        rgns = leaves[:primer_idx][::-1]
    else:
        rgns = leaves[primer_idx + 1 :]

    return (read, rgns)

import io
import os
import gzip
from seqspec.Assay import Assay
from seqspec.Region import Onlist, Region, Read
import yaml
import requests
from Bio import GenBank
from typing import Tuple, List
from packaging import version


def load_spec(spec_fn: str):
    with open(spec_fn, "r") as stream:
        return load_spec_stream(stream)


def load_spec_stream(spec_stream: io.IOBase):
    data: Assay = yaml.load(spec_stream, Loader=yaml.Loader)
    # set the parent id in the Assay object upon loading it
    for r in data.library_spec:
        r.set_parent_id(None)

    # for backwards compatibilty, for specs < v0.3.0 set the files to empty
    for r in data.sequence_spec:
        if version.parse(data.seqspec_version) < version.parse("0.3.0"):
            r.set_files([])

    return data


def load_genbank(gbk_fn: str):
    with open(gbk_fn, "r") as stream:
        return load_genbank_stream(stream)


def load_genbank_stream(gbk_stream: io.IOBase):
    data: GenBank = GenBank.read(gbk_stream)
    return data


class RegionCoordinate:
    def __init__(self, cut_name, cut_type, start, end):
        self.cut_name = cut_name
        self.cut_type = cut_type
        self.start = start
        self.end = end

    def __repr__(self):
        return f"RegionCoordinate {self.cut_name} [{self.cut_type}]: ({self.start}, {self.end})"

    def __str__(self):
        return f"RegionCoordinate {self.cut_name} [{self.cut_type}]: ({self.start}, {self.end})"

    def __eq__(self, other):
        return self.start == other.start and self.end == other.end


def write_read(header, seq, qual, f):
    f.write(f"{header}\n{seq}\n+\n{qual}\n")


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
        r = requests.head(uri)
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
}


# unused
# '#FF8C00'
# '#95A5A6'


def complement_nucleotide(nucleotide):
    complements = {
        "A": "T",
        "T": "A",
        "G": "C",
        "C": "G",
        "R": "Y",
        "Y": "R",
        "S": "S",
        "W": "W",
        "K": "M",
        "M": "K",
        "B": "V",
        "D": "H",
        "V": "B",
        "H": "D",
        "N": "N",
        "X": "X",
    }
    return complements.get(
        nucleotide, "N"
    )  # Default to 'N' if nucleotide is not recognized


def complement_sequence(sequence):
    return "".join(complement_nucleotide(n) for n in sequence.upper())


def map_read_id_to_regions(
    spec: Assay, modality: str, region_id: str
) -> Tuple[Read, List[Region]]:
    # get all atomic elements from library
    leaves = spec.get_libspec(modality).get_leaves()
    # get the read object and primer id
    for i in spec.sequence_spec:
        if i.read_id == region_id:
            read = i
            break
    else:
        raise IndexError(
            "region_id {} not found in reads {}".format(
                region_id, [i.read_id for i in spec.sequence_spec]
            )
        )
    primer_id = read.primer_id
    # get the index of the primer in the list of leaves (ASSUMPTION, 5'->3' and primer is an atomic element)
    for i, l in enumerate(leaves):
        if l.region_id == primer_id:
            primer_idx = i
            break
    else:
        raise IndexError(
            "primer_id {} not found in regions {}".format(
                primer_id, [leaf.region_id for leaf in leaves]
            )
        )
    # If we are on the opposite strand, we go in the opposite way
    if read.strand == "neg":
        rgns = leaves[:primer_idx][::-1]
    else:
        rgns = leaves[primer_idx + 1 :]

    return (read, rgns)

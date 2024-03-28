import io
import gzip
from pathlib import Path
from seqspec.Assay import Assay
from seqspec.Region import Onlist
from urllib.parse import urlparse
import yaml
import requests
from Bio import GenBank


def load_spec(spec_fn: str):
    with open(spec_fn, "r") as stream:
        return load_spec_stream(stream)


def load_spec_stream(spec_stream: io.IOBase):
    data: Assay = yaml.load(spec_stream, Loader=yaml.Loader)
    # set the parent id in the Assay object upon loading it
    for r in data.library_spec:
        r.set_parent_id(None)
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


def read_list(onlist: Onlist):
    """Given an onlist object read the local or remote data
    """
    location, filename = find_onlist_file(onlist)

    stream = None
    try:
        # open stream
        if location == "remote":
            response = requests.get(filename, stream=True)
            response.raise_for_status()
            stream = response.raw
        elif location == "local":
            stream = open(filename, "rb")
        else:
            raise ValueError(
                "Unsupported location {}. Expected remote or local".format(location))

        # do we need to decompress?
        if filename.endswith(".gz"):
            stream = gzip.GzipFile(fileobj=stream)

        # convert to text stream
        stream = io.TextIOWrapper(stream)

        results = list(yield_onlist_contents(stream))
    finally:
        if stream is None:
            print("Warning: unable to open barcode file {}".format(filename))
        else:
            stream.close()

    return results


def find_onlist_file(onlist: Onlist):
    url = urlparse(onlist.filename)
    pathname = Path(url.path)
    basename = Path(pathname.name)
    if basename.exists():
        # we have a copy of the file in this directory
        return ("local", str(basename))
    elif pathname.exists():
        # we have a path to another directory
        return ("local", str(pathname))
    elif url.scheme != '' and onlist.location == "remote":
        # Should we ignore the location if there's a url scheme?
        return ("remote", str(onlist.filename))
    else:
        raise FileNotFoundError(
            "No such {} file {}".format(onlist.location, onlist.filename))


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


def map_read_id_to_regions(spec, modality, region_id):
    # get all atomic elements from library
    leaves = spec.get_libspec(modality).get_leaves()
    # get the read object and primer id
    read = [i for i in spec.sequence_spec if i.read_id == region_id][0]
    primer_id = read.primer_id
    # get the index of the primer in the list of leaves (ASSUMPTION, 5'->3' and primer is an atomic element)
    primer_idx = [i for i, l in enumerate(leaves) if l.region_id == primer_id][0]
    # If we are on the opposite strand, we go in the opposite way
    if read.strand == "neg":
        rgns = leaves[:primer_idx][::-1]
    else:
        rgns = leaves[primer_idx + 1 :]

    return (read, rgns)

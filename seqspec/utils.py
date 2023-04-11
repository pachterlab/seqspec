import io
from seqspec.Assay import Assay
import yaml


def load_spec(spec_fn: str):
    with open(spec_fn, "r") as stream:
        return load_spec_stream(stream)


def load_spec_stream(spec_stream: io.IOBase):
    data: Assay = yaml.load(spec_stream, Loader=yaml.Loader)
    # set the parent id in the Assay object upon loading it
    for r in data.assay_spec:
        r.set_parent_id(None)
    return data


# return cut indices for all atomic regions
def get_cuts(regions, cuts=[]):
    if not cuts:
        cuts = []
    prev = 0
    for r in regions:
        nxt = prev + r.max_len
        cuts.append((prev, nxt))
        prev = nxt
    return cuts


def write_read(header, seq, qual, f):
    f.write(f"{header}\n{seq}\n+\n{qual}\n")

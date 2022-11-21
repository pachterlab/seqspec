from seqspec.Assay import Assay
import yaml


def load_spec(spec_fn: str):
    with open(spec_fn, "r") as stream:
        data: Assay = yaml.load(stream, Loader=yaml.Loader)
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

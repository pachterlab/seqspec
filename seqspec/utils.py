from seqspec.Assay import Assay
import yaml


def load_spec(spec_fn: str):
    with open(spec_fn, "r") as stream:
        data: Assay = yaml.load(stream, Loader=yaml.Loader)
    return data

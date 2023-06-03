from jsonschema import Draft4Validator
import yaml
from os import path

from seqspec.utils import load_spec


def setup_check_args(parser):
    parser_check = parser.add_parser(
        "check",
        description="validate seqspec file",
        help="validate seqspec file",
    )
    parser_check.add_argument("yaml", help="Sequencing specification yaml file")
    parser_check.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
    )
    return parser_check


def validate_check_args(parser, args):
    # if everything is valid the run_check
    spec_fn = args.yaml
    # o = args.o
    schema_fn = path.join(path.dirname(__file__), "schema/seqspec.schema.json")
    # schema_fn = "schema/seqspec.schema.json"
    with open(schema_fn, "r") as stream:
        schema = yaml.load(stream, Loader=yaml.Loader)
    # print(schema)

    spec = load_spec(spec_fn)

    return run_check(schema, spec, spec_fn)  # , o)


def run_check(schema, spec, spec_fn):
    v = Draft4Validator(schema)
    idx = 1
    for idx, error in enumerate(v.iter_errors(spec.to_dict()), 1):
        print(
            f"[error {idx}] {error.message} in spec[{']['.join(repr(index) for index in error.path)}]"
        )
    # get all of the onlist files in the spec and check that they exist relative to the path of the spec
    modes = spec.modalities
    olrgns = []
    for m in modes:
        olrgns += [i.onlist for i in spec.get_modality(m).get_onlist_regions()]

    # check paths relative to spec_fn
    for ol in olrgns:
        if ol.filename[:-3] == ".gz":
            check = path.join(path.dirname(spec_fn), ol.filename[:-3])
            if not path.exists(check):
                print(f"[error {idx}] {ol.filename[:-3]} does not exist")
                idx += 1
        else:
            check = path.join(path.dirname(spec_fn), ol.filename)
            check_gz = path.join(path.dirname(spec_fn), ol.filename + ".gz")
            if not path.exists(check) and not path.exists(check_gz):
                print(f"[error {idx}] {ol.filename} does not exist")
                idx += 1

    # TODO add option to check md5sum

    return idx

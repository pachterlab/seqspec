# from seqspec.Assay import Assay
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

    return run_check(schema, spec)  # , o)


def run_check(schema, spec):

    v = Draft4Validator(schema)
    idx = 0
    for idx, error in enumerate(v.iter_errors(spec), 1):
        print(
            f"[error {idx}] {error.message} in spec[{']['.join(repr(index) for index in error.path)}]"
        )

    return idx

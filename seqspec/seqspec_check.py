from jsonschema import Draft4Validator
import yaml
from os import path

from seqspec.utils import load_spec, file_exists


def setup_check_args(parser):
    subparser = parser.add_parser(
        "check",
        description="validate seqspec file",
        help="validate seqspec file",
    )
    subparser.add_argument("yaml", help="Sequencing specification yaml file")
    subparser.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
    )
    return subparser


def validate_check_args(parser, args):
    # if everything is valid the run_check
    spec_fn = args.yaml
    o = args.o
    schema_fn = path.join(path.dirname(__file__), "schema/seqspec.schema.json")
    # schema_fn = "schema/seqspec.schema.json"
    with open(schema_fn, "r") as stream:
        schema = yaml.load(stream, Loader=yaml.Loader)
    # print(schema)

    spec = load_spec(spec_fn)

    errors = run_check(schema, spec, spec_fn)  # , o)

    if errors:
        if o:
            with open(o, "w") as f:
                print("\n".join(errors), file=f)
        else:
            print("\n".join(errors))

    return


def run_check(schema, spec, spec_fn):
    errors = []
    v = Draft4Validator(schema)
    idx = 1
    for idx, error in enumerate(v.iter_errors(spec.to_dict()), 1):
        errors.append(
            f"[error {idx}] {error.message} in spec[{']['.join(repr(index) for index in error.path)}]"
        )

    # check that the modalities are unique
    if len(spec.modalities) != len(set(spec.modalities)):
        errors.append(
            f"[error {idx}] modalities [{', '.join(spec.modalities)}] are not unique"
        )
        idx += 1

    # check that region_ids of the first level of the spec correspond to the modalities
    # one for each modality
    modes = spec.modalities
    rgns = spec.assay_spec
    for r in rgns:
        rid = r.region_id
        if rid not in modes:
            errors.append(
                f"[error {idx}] region_id '{rid}' of the first level of the spec does not correspond to a modality [{', '.join(modes)}]"
            )
            idx += 1

    # get all of the onlist files in the spec and check that they exist relative to the path of the spec
    modes = spec.modalities
    olrgns = []
    for m in modes:
        olrgns += [i.onlist for i in spec.get_modality(m).get_onlist_regions()]

    # check paths relative to spec_fn
    for ol in olrgns:
        if ol.location == "local":
            if ol.filename[:-3] == ".gz":
                check = path.join(path.dirname(spec_fn), ol.filename[:-3])
                if not path.exists(check):
                    errors.append(f"[error {idx}] {ol.filename[:-3]} does not exist")
                    idx += 1
            else:
                check = path.join(path.dirname(spec_fn), ol.filename)
                check_gz = path.join(path.dirname(spec_fn), ol.filename + ".gz")
                if not path.exists(check) and not path.exists(check_gz):
                    errors.append(f"[error {idx}] {ol.filename} does not exist")
                    idx += 1
        elif ol.location == "remote":
            # ping the link with a simple http request to check if the file exists at that URI
            if not file_exists(ol.filename):
                errors.append(f"[error {idx}] {ol.filename} does not exist")
                idx += 1

    # get all of the regions with type fastq in the spec and check that those files exist relative to the path of the spec
    fqrgns = []
    for m in modes:
        fqrgns += [i for i in spec.get_modality(m).get_region_by_type("fastq")]
        fqrgns += [i for i in spec.get_modality(m).get_region_by_type("fastq_link")]
    for fqrgn in fqrgns:
        if fqrgn.region_type == "fastq":
            check = path.join(path.dirname(spec_fn), fqrgn.region_id)
            if not path.exists(check):
                errors.append(f"[error {idx}] {fqrgn.region_id} does not exist")
                idx += 1
        elif fqrgn.region_type == "fastq_link":
            # ping the link with a simple http request to check if the file exists at that URI
            if not file_exists(fqrgn.region_id):
                errors.append(f"[error {idx}] {fqrgn.region_id} does not exist")
                idx += 1

    # TODO add option to check md5sum

    # check that the region_id is unique across all regions
    rgn_ids = set()
    for m in modes:
        for rgn in spec.get_modality(m).get_leaves():
            if rgn.region_id in rgn_ids:
                errors.append(
                    f"[error {idx}] region_id '{rgn.region_id}' is not unique across all regions"
                )
                idx += 1
            else:
                rgn_ids.add(rgn.region_id)

    # check that sequence length is the same as min_length
    for m in modes:
        for rgn in spec.get_modality(m).get_leaves():
            if rgn.sequence and len(rgn.sequence) < rgn.min_len:
                errors.append(
                    f"[error {idx}] '{rgn.region_id}' sequence '{rgn.sequence}' length '{len(rgn.sequence)}' is less than min_len '{rgn.min_len}'"
                )
                idx += 1

    return errors

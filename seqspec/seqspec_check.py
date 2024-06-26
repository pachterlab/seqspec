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
    rgns = spec.library_spec
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
        olrgns += [i.onlist for i in spec.get_libspec(m).get_onlist_regions()]

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
        fqrgns += [i for i in spec.get_libspec(m).get_region_by_region_type("fastq")]
        fqrgns += [
            i for i in spec.get_libspec(m).get_region_by_region_type("fastq_link")
        ]
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

    # read ids should be unique
    read_ids = set()
    for read in spec.sequence_spec:
        if read.read_id in read_ids:
            errors.append(
                f"[error {idx}] read_id '{read.read_id}' is not unique across all reads"
            )
            idx += 1
        else:
            read_ids.add(read.read_id)

    # iterate through reads in sequence_spec and check that the fastq files exist
    for read in spec.sequence_spec:
        check = path.join(path.dirname(spec_fn), read.read_id)
        if not path.exists(check):
            errors.append(f"[error {idx}] {read.read_id} file does not exist")
            idx += 1

    # check that the primer ids, strand tuple pairs are unique across all reads
    primer_strand_pairs = set()
    for read in spec.sequence_spec:
        if (read.primer_id, read.strand) in primer_strand_pairs:
            errors.append(
                f"[error {idx}] primer_id '{read.primer_id}' and strand '{read.strand}' tuple is not unique across all reads"
            )
            idx += 1
        else:
            primer_strand_pairs.add((read.primer_id, read.strand))

    # TODO add option to check md5sum

    # check that the region_id is unique across all regions
    rgn_ids = set()
    for m in modes:
        for rgn in spec.get_libspec(m).get_leaves():
            if rgn.region_id in rgn_ids:
                errors.append(
                    f"[error {idx}] region_id '{rgn.region_id}' is not unique across all regions"
                )
                idx += 1
            else:
                rgn_ids.add(rgn.region_id)

    # check that the modality is in the reads
    for read in spec.sequence_spec:
        if read.modality not in modes:
            errors.append(
                f"[error {idx}] '{read.read_id}' modality '{read.modality}' does not exist in the modalities"
            )
            idx += 1

    # check that the unique primer ids exist as a region id in the library_spec
    for read in spec.sequence_spec:
        if read.primer_id not in rgn_ids:
            errors.append(
                f"[error {idx}] '{read.read_id}' primer_id '{read.primer_id}' does not exist in the library_spec"
            )
            idx += 1

    # NOTE: this is a strong assumption that may be relaxed in the future
    # check that the primer id for each read is in the leaves of the spec for that modality
    for read in spec.sequence_spec:
        mode = spec.get_libspec(read.modality)
        leaves = mode.get_leaves()
        if read.primer_id not in [i.region_id for i in leaves]:
            errors.append(
                f"[error {idx}] '{read.read_id}' primer_id '{read.primer_id}' does not exist as an atomic region in the library_spec for modality '{read.modality}'"
            )
            idx += 1

    # check that the max read len is not longer than the max len of the lib spec after the primer
    # for read in spec.sequence_spec:
    #     mode = spec.get_libspec(read.modality)
    #     leaves = mode.get_leaves()
    #     idx = [i.region_id for i in leaves].index(read.primer_id)

    # if a region has a sequence type "fixed" then it should not contain subregions
    # if a region has a sequence type "joiend" then it should contain subregions
    # if a region has a sequence type "random" then it should not contain subregions and should be all X's
    # if a region has a sequence type "onlist" then it should have an onlist object
    def seqtype_check(rgn, errors, idx):
        # this is a recursive function that iterates through all regions and checks the sequence type
        if rgn.sequence_type == "fixed" and rgn.regions:
            errors.append(
                f"[error {idx}] '{rgn.region_id}' sequence_type is 'fixed' and contains subregions"
            )
            idx += 1
        if rgn.sequence_type == "joined" and not rgn.regions:
            errors.append(
                f"[error {idx}] '{rgn.region_id}' sequence_type is 'joined' and does not contain subregions"
            )
            idx += 1
        if rgn.sequence_type == "random" and rgn.regions:
            errors.append(
                f"[error {idx}] '{rgn.region_id}' sequence_type is 'random' and contains subregions"
            )
            idx += 1
        if rgn.sequence_type == "random" and rgn.sequence != "X" * rgn.max_len:
            errors.append(
                f"[error {idx}] '{rgn.region_id}' sequence_type is 'random' and sequence is not all X's"
            )
            idx += 1
        if rgn.sequence_type == "onlist" and not rgn.onlist:
            errors.append(
                f"[error {idx}] '{rgn.region_id}' sequence_type is 'onlist' and does not have an onlist object"
            )
            idx += 1
        if rgn.regions:
            for r in rgn.regions:
                errors, idx = seqtype_check(r, errors, idx)
        return (errors, idx)

    for m in modes:
        for rgn in [spec.get_libspec(m)]:
            errors, idx = seqtype_check(rgn, errors, idx)

    # check the lengths of every region against the max_len, using a recursive function
    def len_check(rgn, errors, idx):
        if rgn.regions:
            for r in rgn.regions:
                errors, idx = len_check(r, errors, idx)
        if rgn.max_len < rgn.min_len:
            errors.append(
                f"[error {idx}] '{rgn.region_id}' max_len is less than min_len"
            )
            idx += 1
        return (errors, idx)

    for m in modes:
        for rgn in [spec.get_libspec(m)]:
            errors, idx = len_check(rgn, errors, idx)

    # check that the length of the sequence is equal to the max_len using a recursive function
    # an assumption in the code and spec is that the displayed sequence is equal to the max_len
    def seq_len_check(rgn, errors, idx):
        if rgn.regions:
            for r in rgn.regions:
                errors, idx = seq_len_check(r, errors, idx)
        if rgn.sequence and (
            len(rgn.sequence) < rgn.min_len or len(rgn.sequence) > rgn.max_len
        ):
            # noqa
            errors.append(
                f"[error {idx}] '{rgn.region_id}' sequence '{rgn.sequence}' has length {len(rgn.sequence)}, expected range ({rgn.min_len}, {rgn.max_len})"
            )
            idx += 1
        return (errors, idx)

    for m in modes:
        for rgn in [spec.get_libspec(m)]:
            errors, idx = seq_len_check(rgn, errors, idx)

    return errors

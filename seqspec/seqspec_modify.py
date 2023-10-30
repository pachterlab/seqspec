from seqspec.utils import load_spec


def setup_modify_args(parser):
    # given a spec, a region id and a list of key value property pairs, modify the spec
    subparser = parser.add_parser(
        "modify",
        description="modify region attributes",
        help="modify region attributes",
    )
    subparser_required = subparser.add_argument_group("required arguments")
    subparser.add_argument("yaml", help="Sequencing specification yaml file")

    # Region properties

    subparser.add_argument(
        "--region-id",
        metavar="REGIONID",
        help=("New ID of region"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--region-type",
        metavar="REGIONTYPE",
        help=("New type of region"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--region-name",
        metavar="REGIONNAME",
        help=("New name of region"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--sequence-type",
        metavar="SEQUENCETYPE",
        help=("New type of sequence"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--sequence",
        metavar="SEQUENCE",
        help=("New sequence"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--min-len",
        metavar="MINLEN",
        help=("Min region length"),
        type=int,
        default=None,
    )
    subparser.add_argument(
        "--max-len",
        metavar="MAXLEN",
        help=("Max region length"),
        type=int,
        default=None,
    )

    subparser_required.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
        required=True,
    )
    subparser_required.add_argument(
        "-r",
        metavar="REGIONID",
        help=("ID of region to modify"),
        type=str,
        default=None,
        required=True,
    )
    subparser_required.add_argument(
        "-m",
        metavar="MODALITY",
        help=("Modality of the assay"),
        type=str,
        default=None,
        required=True,
    )

    return subparser


def validate_modify_args(parser, args):
    # if everything is valid the run_format
    fn = args.yaml
    o = args.o
    spec = load_spec(fn)
    modality = args.m
    target_region = args.r

    region_id = args.region_id
    region_type = args.region_type
    region_name = args.region_name
    sequence_type = args.sequence_type
    sequence = args.sequence

    min_len = args.min_len
    max_len = args.max_len
    kwd = {
        "region_id": region_id,
        "region_type": region_type,
        "name": region_name,
        "sequence_type": sequence_type,
        "sequence": sequence,
        "min_len": min_len,
        "max_len": max_len,
    }
    spec = run_modify(spec, modality, target_region, **kwd)
    # update region in spec
    # once the region is updated, update the spec
    spec.update_spec()
    spec.to_YAML(o)


def run_modify(
    spec,
    modality,
    target_region,
    region_id,
    region_type,
    name,
    sequence_type,
    sequence,
    min_len,
    max_len,
):
    spec.get_modality(modality).update_region_by_id(
        target_region,
        region_id,
        region_type,
        name,
        sequence_type,
        sequence,
        min_len,
        max_len,
    )

    return spec

from seqspec.utils import load_spec


def setup_modify_args(parser):
    # given a spec, a region id and a list of key value property pairs, modify the spec
    subparser = parser.add_parser(
        "modify",
        description="format seqspec file",
        help="format seqspec file",
    )
    subparser.add_argument("yaml", help="Sequencing specification yaml file")
    subparser.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "-r",
        metavar="REGIONID",
        help=("ID of region to modify"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "-m",
        metavar="modality",
        help=("Modality of the assay"),
        type=str,
        default=None,
    )

    # Region properties

    subparser.add_argument(
        "--region-id",
        metavar=f"REGIONID",
        help=("New ID of region"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--region-type",
        metavar=f"REGIONTYPE",
        help=("New type of region"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--region-name",
        metavar=f"REGIONNAME",
        help=("New name of region"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--sequence-type",
        metavar=f"SEQUENCETYPE",
        help=("New type of sequence"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--sequence",
        metavar=f"SEQUENCE",
        help=("New sequence"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--min-len",
        metavar=f"MINLEN",
        help=("Min region length"),
        type=int,
        default=None,
    )
    subparser.add_argument(
        "--max-len",
        metavar=f"MAXLEN",
        help=("Max region length"),
        type=int,
        default=None,
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

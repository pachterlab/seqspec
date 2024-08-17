from seqspec.utils import load_spec
from seqspec.Region import File


def setup_modify_args(parser):
    # given a spec, a region id and a list of key value property pairs, modify the spec
    subparser = parser.add_parser(
        "modify",
        description="modify region attributes",
        help="modify region attributes",
    )
    subparser_required = subparser.add_argument_group("required arguments")
    subparser.add_argument("yaml", help="Sequencing specification yaml file")

    subparser.add_argument(
        "--region",
        help=("Switch to region mode"),
        action="store_true",
        default=False,
    )

    # Read properties
    subparser.add_argument(
        "--read-id",
        metavar="READID",
        help=("New ID of read"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--read-name",
        metavar="READNAME",
        help=("New name of read"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--primer-id",
        metavar="PRIMERID",
        help=("New ID of primer"),
        type=str,
        default=None,
    )
    subparser.add_argument(
        "--strand",
        metavar="STRAND",
        help=("New strand"),
        type=str,
        default=None,
    )

    # files to insert into the read
    # format: filename,filetype,filesize,url,urltype,md5:...
    subparser.add_argument(
        "--files",
        metavar="FILES",
        help=("New files, (filename,filetype,filesize,url,urltype,md5:...)"),
        type=str,
        default=None,
    )

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
        metavar="READID/REGIONID",
        help=("ID of read/region to modify"),
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
    target_r = args.r

    # Read properties
    read_id = args.read_id
    read_name = args.read_name
    primer_id = args.primer_id
    strand = args.strand
    files = args.files

    # Region properties
    region_id = args.region_id
    region_type = args.region_type
    region_name = args.region_name
    sequence_type = args.sequence_type
    sequence = args.sequence

    # Read and Region properties
    min_len = args.min_len
    max_len = args.max_len

    read_kwd = {
        "read_id": read_id,
        "read_name": read_name,
        "primer_id": primer_id,
        "min_len": min_len,
        "max_len": max_len,
        "strand": strand,
        "files": files,
    }

    region_kwd = {
        "region_id": region_id,
        "region_type": region_type,
        "name": region_name,
        "sequence_type": sequence_type,
        "sequence": sequence,
        "min_len": min_len,
        "max_len": max_len,
    }
    if args.region:
        spec = run_modify_region(spec, modality, target_r, **region_kwd)
    else:
        spec = run_modify_read(spec, modality, target_r, **read_kwd)
    # update region in spec
    # once the region is updated, update the spec
    spec.update_spec()
    spec.to_YAML(o)


def run_modify_read(
    spec,
    modality,
    target_read,
    read_id,
    read_name,
    primer_id,
    min_len,
    max_len,
    strand,
    files,
):
    reads = spec.get_seqspec(modality)
    if files:
        files = parse_files_string(files)
    for r in reads:
        if r.read_id == target_read:
            r.update_read_by_id(
                read_id, read_name, modality, primer_id, min_len, max_len, strand, files
            )

    return spec


def run_modify_region(
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
    spec.get_libspec(modality).update_region_by_id(
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


# filename,filetype,filesize,url,urltype,md5:...
def parse_files_string(input_string):
    files = []
    objects = input_string.split(":")
    for obj in objects:
        parts = obj.split(",")
        filename, filetype, filesize, url, urltype, md5 = parts

        file = File(
            filename=filename,
            filetype=filetype,
            filesize=int(filesize),
            url=url,
            urltype=urltype,
            md5=md5,
        )
        files.append(file)

    return files

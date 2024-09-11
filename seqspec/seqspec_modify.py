from seqspec.utils import load_spec
from seqspec.File import File
from argparse import RawTextHelpFormatter, SUPPRESS
import warnings


# TODO fix modify to use the -s selector
def setup_modify_args(parser):
    # given a spec, a region id and a list of key value property pairs, modify the spec
    subparser = parser.add_parser(
        "modify",
        description="""
Modify attributes of various elements in a seqspec file.

Examples:
seqspec modify -m rna -o mod_spec.yaml -i rna_R1 --read-id renamed_rna_R1 spec.yaml                                                                                                # modify the read id
seqspec modify -m rna -o mod_spec.yaml -s region -i rna_cell_bc --region-id renamed_rna_cell_bc spec.yaml                                                                        # modify the region id
seqspec modify -m rna -o mod_spec.yaml -i rna_R1 --files "R1_1.fastq.gz,fastq,0,./fastq/R1_1.fastq.gz,local,null:R1_2.fastq.gz,fastq,0,./fastq/R1_2.fastq.gz,local,null" spec.yaml # modify the files for R1 fastq
---
""",
        help="Modify attributes of various elements in seqspec file",
        formatter_class=RawTextHelpFormatter,
    )
    subparser_required = subparser.add_argument_group("required arguments")
    subparser.add_argument("yaml", help="Sequencing specification yaml file")

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

    # Read or Region properties
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

    subparser.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
        required=False,
    )
    subparser_required.add_argument(
        "-r",
        metavar="READID/REGIONID",
        help=SUPPRESS,
        type=str,
        default=None,
        required=False,
    )
    subparser_required.add_argument(
        "-i",
        metavar="IDs",
        help=("IDs"),
        type=str,
        default=None,
        required=False,
    )
    choices = ["read", "region"]
    subparser.add_argument(
        "-s",
        metavar="SELECTOR",
        help=(f"Selector for ID, [{', '.join(choices)}] (default: read)"),
        type=str,
        default="read",
        choices=choices,
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
    if args.r is not None:
        warnings.warn(
            "The '-r' argument is deprecated and will be removed in a future version. "
            "Please use '-i' instead.",
            DeprecationWarning,
        )
        # Optionally map the old option to the new one
        if not args.i:
            args.i = args.r

    # if everything is valid the run_format
    fn = args.yaml
    o = args.o
    modality = args.m
    # target_r = args.r
    idtype = args.s  # selector
    ids = args.i

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

    spec = load_spec(fn)

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

    if idtype == "region":
        spec = run_modify_region(spec, modality, ids, **region_kwd)
    elif idtype == "read":
        spec = run_modify_read(spec, modality, ids, **read_kwd)
    # update region in spec
    # once the region is updated, update the spec
    spec.update_spec()
    if o:
        spec.to_YAML(o)
    else:
        print(spec.to_YAML())


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
            file_id=filename,
            filename=filename,
            filetype=filetype,
            filesize=int(filesize),
            url=url,
            urltype=urltype,
            md5=md5,
        )
        files.append(file)

    return files

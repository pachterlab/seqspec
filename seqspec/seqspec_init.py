from seqspec.Assay import Assay
from seqspec.Region import Region
from seqspec.File import File
from seqspec.Read import Read
from typing import List
import newick

# example


# seqspec init -n myassay -m 1 -o spec.yaml "(((barcode:16,umi:12)r1.fastq.gz,(cdna:150)r2.fastq.gz)rna)"
# seqspec init -n myassay -m 1 -o spec.yaml -r "rna,R1.fastq.gz,truseq_r1,16,pos:rna,R2.fastq.gz,truseq_r2,100,neg" "((truseq_r1:10,barcode:16,umi:12,cdna:150)rna)"
# seqspec init -n myassay -m 2 -o spec.yaml "(((barcode:16,umi:12)r1.fastq.gz,(cdna:150)r2.fastq.gz)rna,((barcode:16)r1.fastq.gz,(gdna:150)r2.fastq.gz,(gdna:150)r3.fastq.gz)atac)"
def setup_init_args(parser):
    subparser = parser.add_parser(
        "init",
        description="init a seqspec file",
        help="init a seqspec file",
    )
    subparser_required = subparser.add_argument_group("required arguments")
    subparser_required.add_argument(
        "-n", metavar="NAME", type=str, help="assay name", required=True
    )
    subparser_required.add_argument(
        "-m", metavar="MODALITIES", type=int, help="number of modalities", required=True
    )

    # -r "rna,R1.fastq.gz,truseq_r1,16,pos:rna,R2.fastq.gz,truseq_r2,100,neg"
    subparser_required.add_argument(
        "-r",
        metavar="READS",
        type=str,
        help="list of modalities, reads, primer_ids, lengths, and strand (e.g. modality,fastq_name,primer_id,len,strand:...)",
        required=True,
    )

    subparser.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
    )
    subparser.add_argument("newick", help=("tree in newick format"))
    return subparser


def validate_init_args(parser, args):
    name = args.n
    modalities = args.m
    newick_str = args.newick
    o = args.o
    reads_str = args.r

    if newick_str is None:
        parser.error("modality-FASTQs pairs must be provided")

    return run_init(name, modalities, newick_str, reads_str, o)


def run_init(name: str, modalities, newick_str, reads_str, o=None):
    reads = parse_reads_string(reads_str)
    tree = newick.loads(newick_str)
    if len(tree[0].descendants) != modalities:
        raise ValueError(
            "Number of modalities must match number of modality-FASTQs pairs"
        )

    reads = parse_reads_string(reads_str)
    spec = init(name, tree[0].descendants, reads)

    if o:
        spec.to_YAML(o)
    else:
        print(spec.to_YAML())

    return


def init(name: str, tree: List[newick.Node], reads: List[Read]):
    # make read for each fastq
    # make region for each modality
    # add modality regions to assay
    rgns = []
    mnames = []
    for t in tree:
        r = Region(region_id="", region_type="", name="", sequence_type="")
        rgns.append(newick_to_region(t, r))
        mnames.append(t.name)

    assay = Assay(
        assay_id="",
        name=name,
        doi="",
        date="",
        description="",
        modalities=mnames,
        lib_struct="",
        library_kit="",
        library_protocol="",
        sequence_kit="",
        sequence_protocol="",
        sequence_spec=reads,
        library_spec=rgns,
    )
    return assay


def newick_to_region(
    node, region=Region(region_id="", region_type="", name="", sequence_type="")
):
    region.region_id = node.name
    region.name = node.name

    if len(node.descendants) == 0:
        region.min_len = int(node.length)
        region.max_len = int(node.length)
        return region
    region.regions = []
    for n in node.descendants:
        region.regions.append(
            newick_to_region(
                n,
                Region(region_id=n.name, region_type="", name=n.name, sequence_type=""),
            )
        )
    return region


def parse_reads_string(input_string):
    reads = []
    objects = input_string.split(":")
    for obj in objects:
        parts = obj.split(",")
        modality, read_id, primer_id, min_len, strand = parts

        read = Read(
            read_id=read_id,
            name=read_id,
            modality=modality,
            primer_id=primer_id,
            min_len=int(min_len),
            max_len=int(min_len),
            strand=strand,
            files=[
                File(
                    file_id=read_id,
                    filename=read_id,
                    filetype="",
                    filesize=0,
                    url="",
                    urltype="",
                    md5="",
                )
            ],
        )
        reads.append(read)

    return reads

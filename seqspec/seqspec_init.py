from seqspec.Assay import Assay
from seqspec.Region import Region
from typing import List
import newick

# example


# seqspec init -n myassay -m 1 -o spec.yaml "(((barcode:16,umi:12)r1.fastq.gz,(cdna:150)r2.fastq.gz)rna)"
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

    subparser_required.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
        required=True,
    )
    subparser.add_argument("newick", help=("tree in newick format"))
    return subparser


def validate_init_args(parser, args):
    # if everything is valid the run_init
    name = args.n
    modalities = args.m
    newick_str = args.newick
    o = args.o
    if newick is None:
        raise ValueError("modality-FASTQs pairs must be provided")

    tree = newick.loads(newick_str)
    if len(tree[0].descendants) != modalities:
        raise ValueError(
            "Number of modalities must match number of modality-FASTQs pairs"
        )

    # load in two specs
    spec = run_init(name, tree[0].descendants)
    spec.to_YAML(o)


# takes in assay_spec list of nodes
def run_init(name: str, tree: List[newick.Node]):
    # make regions for each fastq
    # make region for each modality
    # add fastq regions to modality regions
    # add modality regions to assay
    rgns = []
    mnames = []
    for t in tree:
        r = Region(region_id="", region_type="", name="", sequence_type="")
        rgns.append(newick_to_region(t, r))
        mnames.append(t.name)

    assay = Assay(
        assay="",
        sequencer="",
        name=name,
        doi="",
        publication_date="",
        description="",
        modalities=mnames,
        lib_struct="",
        assay_spec=rgns,
    )

    return assay


# nw = "((barcode,umi)r1.fastq.gz,(cdna)r2.fastq.gz)rna;"
# wn = "rna(r1.fastq.gz(barcode,umi),r1.fastq.gz(cdna));"
# ex = {"rna": [{"r1.fastq.gz": [{"barcode": "barcode"}, {"umi": "umi"}]}, {"r2.fastq.gz": [{"cdna": "cdna"}]}]}
# tree = newick.loads(nw)
# print(tree[0].ascii_art())
# user writes newick format cli and gets an initialized spec file
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

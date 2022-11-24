from seqspec.utils import load_spec


def setup_print_args(parser):
    parser_print = parser.add_parser(
        "print",
        description="print seqspec file",
        help="print seqspec file",
    )
    parser_print.add_argument("yaml", help="Sequencing specification yaml file")
    parser_print.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
    )
    return parser_print


def validate_print_args(parser, args):
    # if everything is valid the run_print
    fn = args.yaml
    o = args.o
    spec = load_spec(fn)
    s = run_print(spec)
    if o:
        with open(o, "w") as f:
            print(s, file=f)
    else:
        print(s)


def run_print(data):
    header = headerTemplate(data.name, data.doi, data.description, data.modalities)
    header2 = "## Final Library"
    assay_spec = multiModalTemplate(data.assay_spec)
    s = f"{header}\n{header2}\n{assay_spec}"
    return s


def headerTemplate(name, doi, description, modalities):
    s = f"""# {name}
- DOI: [{doi}]({doi})
- Description: {description}
- Modalities: {", ".join(modalities)}
    """
    return s


def atomicRegionTemplate(
    name, region_type, sequence_type, sequence, min_len, max_len, onlist, ns=0
):
    s = f"""<details><summary>{name}</summary>

{' '*ns}- region_type: {region_type}
{' '*ns}- sequence_type: {sequence_type}
{' '*ns}- sequence: <pre style="overflow-x: auto; text-align: left; margin: 0; display: inline;">{sequence}</pre>
{' '*ns}- min_len: {min_len}
{' '*ns}- max_len: {max_len}
{' '*ns}- onlist: {onlist}
{' '*ns}</details>"""
    return s


def regionsTemplate(regions):
    s = "\n".join(
        [
            f"{idx + 1}. "
            + atomicRegionTemplate(
                v.name,
                v.region_type,
                v.sequence_type,
                v.sequence,
                v.min_len,
                v.max_len,
                v.onlist,
                len(str(idx + 1))
                + 1
                + 1,  # length of string rep of number plus 1 for "." plus 1 for space
            )
            for idx, v in enumerate(regions)
        ]
    )
    return s


def libStructTemplate(region):
    s = f"""###### {region.name}
<pre style="overflow-x: auto; text-align: left; background-color: #f6f8fa">{region.sequence}</pre>"""
    return s


def multiModalTemplate(assay_spec):
    s = "\n".join(
        [libStructTemplate(v) + "\n" + regionsTemplate(v.regions) for v in assay_spec]
    )
    return s

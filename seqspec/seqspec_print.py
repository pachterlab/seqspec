from seqspec.Assay import Assay
import yaml


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
    run_print(fn, o)


def run_print(fn, o):
    with open(fn, "r") as stream:
        data: Assay = yaml.load(stream, Loader=yaml.Loader)
    print_markdown(data)
    # data.update_spec()
    # data.to_YAML(o)


def headerTemplate(name, doi, description, modalities):
    s = f"""# {name}
- DOI: [{doi}]({doi})
- Description: {description}
- Modalities: {", ".join(modalities)}
    """
    return s


def atomicRegionTemplate(name, sequence_type, sequence, min_len, max_len, onlist, ns=0):
    s = f"""<details><summary>{name}</summary>

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
                v.sequence_type,
                v.sequence,
                v.min_len,
                v.max_len,
                v.onlist,
                len(str(idx + 1))
                + 1
                + 1,  # length of string rep of number plus 1 for "." plus 1 for space
            )
            for idx, (_, v) in enumerate(regions.items())
        ]
    )
    return s


def libStructTemplate(region):
    s = f"""###### {region.name}
<pre style="overflow-x: auto; text-align: left; background-color: #f6f8fa">{region.sequence}</pre>"""
    return s


def multiModalTemplate(assay_spec):
    s = "\n".join(
        [
            libStructTemplate(assay_spec[k])
            + "\n"
            + regionsTemplate(assay_spec[k].join.regions)
            for k, v in assay_spec.items()
        ]
    )
    return s


def print_markdown(data):
    print(headerTemplate(data.name, data.doi, data.description, data.modalities))
    print("## Final Library")
    print(multiModalTemplate(data.assay_spec))


# // console.log(
# //   // headerTemplate(data.name, data.doi, data.description, data.modalities),
# //   // atomicRegionTemplate(
# //   //   data.assay_spec.RNA.join.regions.illumina_p5.name,
# //   //   data.assay_spec.RNA.join.regions.illumina_p5.sequence_type,
# //   //   data.assay_spec.RNA.join.regions.illumina_p5.sequence,
# //   //   data.assay_spec.RNA.join.regions.illumina_p5.min_len,
# //   //   data.assay_spec.RNA.join.regions.illumina_p5.max_len,
# //   //   data.assay_spec.RNA.join.regions.illumina_p5.onlist
# //   // ),
# //   regionsTemplate(data.assay_spec.RNA.join.regions)
# // );


# function htmlTemplate(data) {
#   return `
#   <!DOCTYPE html>
#   <html>
#     <head>
#       <meta name="viewport" content="width=device-width, initial-scale=1" />
#       <link rel="stylesheet" type="../text/css" href="styles.css" />
#     </head>
#     <body>
#       <div style="width: 75%; margin: 0 auto">
#         <h6><a href="../index.html">Back</a></h6>
#         <div id="assay">
#           {headerTemplate(
#             data.name,
#             data.doi,
#             data.description,
#             data.modalities
#           )}
#         </div>
#         <div id="assay_spec">
#           <h2>Final library</h2>
#           {multiModalTemplate(data.assay_spec)}
#         </div>
#       </div>
#     </body>
#   </html>
#   `;
# }

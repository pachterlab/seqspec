from seqspec.utils import load_spec
from seqspec.seqspec_print_html import run_print_html
import newick
from .utils import REGION_TYPE_COLORS


def setup_print_args(parser):
    subparser = parser.add_parser(
        "print",
        description="print seqspec file",
        help="print seqspec file",
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
        "-f",
        metavar="FORMAT",
        help=("Format"),
        type=str,
        default="tree",
        choices=["tree", "html", "png"],
    )
    return subparser


def validate_print_args(parser, args):
    # if everything is valid the run_print
    fn = args.yaml
    o = args.o
    fmt = args.f
    spec = load_spec(fn)
    CMD = {
        "tree": run_print_tree,
        "html": run_print_html,
        "png": run_print_png,
    }
    s = CMD[fmt](spec)
    if fmt == "png":
        s.savefig(o, dpi=300, bbox_inches="tight")
        return
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


def run_print_tree(spec):
    t = []
    for r in spec.assay_spec:
        t.append(r.to_newick())
    n = ",".join(t)
    # print(n)
    tree = newick.loads(f"({n})")
    return tree[0].ascii_art()


def argsort(arr):
    # http://stackoverflow.com/questions/3382352/equivalent-of-numpy-argsort-in-basic-python/3382369#3382369
    # by unutbu
    return sorted(range(len(arr)), key=arr.__getitem__)


def run_print_png(spec):
    # builds directly off of https://colab.research.google.com/drive/1ZCIGrwLEIfE0yo33bP8uscUNPEn1p1DH developed by https://github.com/LucasSilvaFerreira

    # modality
    modalities = spec.list_modalities()
    modes = [spec.get_modality(m) for m in modalities]
    lengths = [i.min_len for i in modes]
    nmodes = len(modalities)

    # sort the modalities by their lengths
    asort = argsort(lengths)
    modalities = [modalities[i] for i in asort]
    lengths = [lengths[i] for i in asort]
    modes = [modes[i] for i in asort]
    assay = spec.assay

    fig, _ = plot_png(assay, modalities, modes, nmodes, lengths)
    return fig


def plot_png(assay, modalities, modes, nmodes, lengths):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    import matplotlib.patches as mpatches

    fsize = 15
    plt.rcParams.update({"font.size": fsize})

    fig, ax = plt.subplots(
        figsize=(10, 1 * nmodes), nrows=nmodes, constrained_layout=True
    )
    fig.suptitle(assay)
    rts = []
    for m, ax in zip(modes, fig.get_axes()):
        # get leaves
        leaves = m.get_leaves()

        # setup plotting variables
        y = 0
        x = 0
        height = 1

        for idx, node in enumerate(leaves):
            # region tupe
            rtype = node.region_type.lower()
            # add to the global list so we can make a legend
            rts.append(rtype)
            # get region properties
            length = node.min_len
            label = f"{length}"

            # setup rectangle for the region
            rectangle = Rectangle(
                (x, y), length, height, color=REGION_TYPE_COLORS[rtype], ec="black"
            )

            # write in the length of the region in the rectangle
            ax.text(
                x + length / 2,
                y + height / 2,
                label,
                horizontalalignment="center",
                verticalalignment="center",
            )  # , rotation=90)
            # add the rectangle
            ax.add_patch(rectangle)

            # add length to x for next region
            x += length

        ax.autoscale()

        # since all axes use the same scale, set the xlim to be 0 to the max length
        ax.set(**{"xlim": (0, max(lengths))})

        # hide the spines
        ax.spines[["right", "top", "left", "bottom"]].set_visible(False)
        # Hide the axis and ticks and labels
        ax.xaxis.set_visible(False)
        ax.set_yticklabels([])
        ax.set_yticks([])

        # label the modality on the ylabel
        ax.set_ylabel(m.region_type, rotation=0, fontsize=20, ha="right", va="center")

    # adjust the xaxis for the last modality to show the length
    ax.xaxis.set_visible(True)
    ax.spines[["bottom"]].set_visible(True)
    ax.minorticks_on()

    ax.set(
        **{
            "xlabel": "# nucleotides",
        }
    )

    # setup the figure legend
    handles = []
    for t in sorted(set(rts)):
        handles.append(mpatches.Patch(color=REGION_TYPE_COLORS[t], label=t))
    fig.legend(handles=handles, loc="center", bbox_to_anchor=(1.1, 0.55))
    return (fig, ax)


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

from seqspec.utils import load_spec
from seqspec.seqspec_print_html import run_print_html
import newick
from .utils import REGION_TYPE_COLORS, complement_sequence
from seqspec.Region import project_regions_to_coordinates


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

    format_choices = ["library", "sequence", "libseq"]
    subparser.add_argument(
        "-s",
        metavar="SPEC",
        help=(
            f"Specification to print, default: library ({', '.join(format_choices)})"
        ),
        type=str,
        default="library",
        choices=format_choices,
    )
    # TODO: fix naming convention: sequence -> seqspec,
    # add libspec (list of regions tab delimited)
    # change tree -> libspec-tree
    #
    # actually, add -s which clarifies which spec to print (library or sequence)
    # then -f should have tree, png, html, sequence
    format_choices = ["tree", "html", "png", "sequence", "info"]
    subparser.add_argument(
        "-f",
        metavar="FORMAT",
        help=(f"Format ({', '.join(format_choices)}), default: tree"),
        type=str,
        default="tree",
        choices=format_choices,
    )

    return subparser


def validate_print_args(parser, args):
    # if everything is valid the run_print
    fmt = args.f
    spectype = args.s

    # validate fmt and spectype pairs, only some are valid
    if fmt == "png" and spectype != "library":
        raise ValueError("-f png only valid for -s library")
    if fmt == "tree" and spectype != "library":
        raise ValueError("-f tree only valid for -s library")
    if fmt == "html" and spectype != "library":
        raise ValueError("-f html only valid for -s library")
    if fmt == "info" and spectype != "sequence":
        raise ValueError("-f info only valid for -s sequence")
    if fmt == "sequence" and spectype != "libseq":
        raise ValueError("-f sequence only valid for -s libseq")

    fn = args.yaml
    o = args.o
    spec = load_spec(fn)

    LIBSEQ_CMD = {
        "sequence": run_print_libseq_sequence,
    }

    SEQUENCE_CMD = {
        "info": run_print_sequence_spec,
    }
    LIBRARY_CMD = {
        "tree": run_print_library_tree,
        "html": run_print_html,
        "png": run_print_library_png,
    }
    CMD = {
        "library": LIBRARY_CMD,
        "sequence": SEQUENCE_CMD,
        "libseq": LIBSEQ_CMD,
    }

    s = CMD[spectype][fmt](spec)
    if fmt == "png":
        s.savefig(o, dpi=300, bbox_inches="tight")
        return
    if o:
        with open(o, "w") as f:
            print(s, file=f)
    else:
        print(s)


def run_print_libseq_sequence(spec):
    p = []
    for modality in spec.modalities:
        p.append(libseq(spec, modality))
    return "\n".join(p)


def libseq(spec, modality):
    libspec = spec.get_libspec(modality)
    seqspec = spec.get_seqspec(modality)

    p = []
    n = []
    leaves = libspec.get_leaves()
    cuts = project_regions_to_coordinates(leaves)
    for idx, read in enumerate(seqspec, 1):
        read_len = read.max_len
        read_id = read.read_id
        primer_id = read.primer_id
        primer_idx = [i for i, l in enumerate(leaves) if l.region_id == primer_id][0]
        primer_pos = cuts[primer_idx]
        if read.strand == "pos":
            wsl = primer_pos.stop - 1
            ws = wsl * " "

            arrowl = read_len - 1
            arrow = arrowl * "-"

            p.append(f"{ws}|{arrow}>({idx}) {read_id}")
        elif read.strand == "neg":
            wsl = primer_pos.start - read_len
            ws = wsl * " "

            arrowl = read_len - 1
            arrow = arrowl * "-"

            n.append(f"{ws}<{arrow}|({idx}) {read_id}")

    s = "\n".join(
        [
            modality,
            "---",
            "\n".join(p),
            libspec.sequence,
            complement_sequence(libspec.sequence),
            "\n".join(n),
        ]
    )
    return s


def run_print(data):
    header = headerTemplate(data.name, data.doi, data.description, data.modalities)
    header2 = "## Final Library"
    library_spec = multiModalTemplate(data.library_spec)
    s = f"{header}\n{header2}\n{library_spec}"
    return s


def run_print_sequence_spec(spec):
    p = []
    for r in spec.sequence_spec:
        p.append(
            "\t".join(
                [r.read_id, r.primer_id, r.strand, str(r.min_len), str(r.max_len)]
            )
        )
    return "\n".join(p)


def run_print_library_tree(spec):
    t = []
    for r in spec.library_spec:
        t.append(r.to_newick())
    n = ",".join(t)
    # print(n)
    tree = newick.loads(f"({n})")
    return tree[0].ascii_art()


def argsort(arr):
    # http://stackoverflow.com/questions/3382352/equivalent-of-numpy-argsort-in-basic-python/3382369#3382369
    # by unutbu
    return sorted(range(len(arr)), key=arr.__getitem__)


def run_print_library_png(spec):
    # builds directly off of https://colab.research.google.com/drive/1ZCIGrwLEIfE0yo33bP8uscUNPEn1p1DH developed by https://github.com/LucasSilvaFerreira

    # modality
    modalities = spec.list_modalities()
    modes = [spec.get_libspec(m) for m in modalities]
    lengths = [i.min_len for i in modes]
    nmodes = len(modalities)

    # sort the modalities by their lengths
    asort = argsort(lengths)
    modalities = [modalities[i] for i in asort]
    lengths = [lengths[i] for i in asort]
    modes = [modes[i] for i in asort]
    assay_id = spec.assay_id

    fig, _ = plot_png(assay_id, modalities, modes, nmodes, lengths)
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
        for spine in ["right", "top", "left", "bottom"]:
            ax.spines[spine].set_visible(False)
        # Hide the axis and ticks and labels
        ax.xaxis.set_visible(False)
        ax.set_yticklabels([])
        ax.set_yticks([])

        # label the modality on the ylabel
        ax.set_ylabel(m.region_type, rotation=0, fontsize=20, ha="right", va="center")

    # adjust the xaxis for the last modality to show the length
    ax.xaxis.set_visible(True)
    ax.spines["bottom"].set_visible(True)
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


def multiModalTemplate(library_spec):
    s = "\n".join(
        [libStructTemplate(v) + "\n" + regionsTemplate(v.regions) for v in library_spec]
    )
    return s

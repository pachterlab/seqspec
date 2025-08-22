"""Print module for seqspec CLI.

This module provides functionality to print sequence and/or library structure
in various formats (ascii, png, html).
"""

import math
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path
from typing import Any, List, Tuple

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import newick
import numpy as np
from matplotlib.patches import FancyArrowPatch, Rectangle

from seqspec.Assay import Assay
from seqspec.Region import complement_sequence
from seqspec.seqspec_index import project_regions_to_coordinates
from seqspec.seqspec_print_html import print_seqspec_html
from seqspec.seqspec_print_utils import libseq
from seqspec.utils import REGION_TYPE_COLORS, load_spec


def setup_print_args(parser) -> ArgumentParser:
    """Create and configure the print command subparser.

    Args:
        parser: The main argument parser to add the print subparser to.

    Returns:
        The configured print subparser.
    """
    subparser = parser.add_parser(
        "print",
        description="""
Print sequence and/or library structure as ascii, png, or html.

Examples:
seqspec print spec.yaml                            # Print the library structure as ascii
seqspec print -f seqspec-ascii spec.yaml           # Print the sequence and library structure as ascii
seqspec print -f seqspec-html spec.yaml            # Print the sequence and library structure as html
seqspec print -o spec.png -f seqspec-png spec.yaml # Print the library structure as a png
---
        """,
        help="Display the sequence and/or library structure from seqspec file",
        formatter_class=RawTextHelpFormatter,
    )

    subparser.add_argument("yaml", type=Path, help="Sequencing specification yaml file")
    subparser.add_argument(
        "-o",
        "--output",
        metavar="OUT",
        type=Path,
        help="Path to output file",
        default=None,
    )

    format_choices = ["library-ascii", "seqspec-html", "seqspec-png", "seqspec-ascii"]
    subparser.add_argument(
        "-f",
        "--format",
        metavar="FORMAT",
        help=f"Format ({', '.join(format_choices)}), default: library-ascii",
        type=str,
        default="library-ascii",
        choices=format_choices,
    )

    return subparser


def validate_print_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the print command arguments.

    Args:
        parser: The argument parser.
        args: The parsed arguments.

    Raises:
        parser.error: If any validation fails.
    """
    if not Path(args.yaml).exists():
        parser.error(f"Input file does not exist: {args.yaml}")

    if args.output and Path(args.output).exists() and not Path(args.output).is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")


def run_print(parser: ArgumentParser, args: Namespace) -> None:
    """Run the print command.

    Args:
        parser: The argument parser.
        args: The parsed arguments.
    """

    validate_print_args(parser, args)

    spec = load_spec(args.yaml)
    result = seqspec_print(spec, args.format)

    if args.output:
        if args.format == "seqspec-png":
            result.savefig(args.output, dpi=300, bbox_inches="tight")
        else:
            with open(args.output, "w") as f:
                print(result, file=f)
    else:
        if args.format == "seqspec-png":
            plt.show()
        else:
            print(result)


def seqspec_print(spec: Assay, fmt: str):
    """Print sequence specification in the specified format.

    Args:
        spec: The seqspec specification to print
        fmt: The format to print in (library-ascii, seqspec-html, seqspec-png, seqspec-ascii)

    Returns:
        The formatted output (string or matplotlib figure)

    Raises:
        ValueError: If format is not supported
    """
    # Map format to print function
    format_to_function = {
        "library-ascii": print_library_ascii,
        "seqspec-html": print_seqspec_html,
        "seqspec-png": print_seqspec_png,
        "seqspec-ascii": print_seqspec_ascii,
    }

    if fmt not in format_to_function:
        raise ValueError(
            f"Unsupported format: {fmt}. Must be one of {list(format_to_function.keys())}"
        )

    return format_to_function[fmt](spec)


def print_seqspec_ascii(spec: Assay) -> str:
    """Print sequence specification in ASCII format.

    Args:
        spec: The seqspec specification to print.

    Returns:
        The ASCII formatted string.
    """
    parts = []
    for modality in spec.modalities:
        parts.append(format_libseq(spec, modality, *libseq(spec, modality)))
    return "\n".join(parts)


def format_libseq(spec: Assay, modality: str, p: List[str], n: List[str]) -> str:
    """Format library sequence for a specific modality.

    Args:
        spec: The seqspec specification.
        modality: The modality to format.
        p: Positive strand parts.
        n: Negative strand parts.

    Returns:
        The formatted string.
    """
    libspec = spec.get_libspec(modality)

    return "\n".join(
        [
            modality,
            "---",
            "\n".join(p),
            libspec.sequence,
            complement_sequence(libspec.sequence),
            "\n".join(n),
        ]
    )


def print_library_ascii(spec: Assay) -> str:
    """Print library structure in ASCII format.

    Args:
        spec: The seqspec specification to print.

    Returns:
        The ASCII formatted string.
    """
    trees = []
    for r in spec.library_spec:
        trees.append(r.to_newick())
    tree_str = ",".join(trees)
    tree = newick.loads(f"({tree_str})")
    return tree[0].ascii_art()


def print_seqspec_png(spec: Assay):
    """Print sequence specification as PNG.

    Args:
        spec: The seqspec specification to print.

    Returns:
        The matplotlib figure.
    """
    modalities = spec.list_modalities()
    modes = [spec.get_libspec(m) for m in modalities]
    lengths = [i.min_len for i in modes]
    nmodes = len(modalities)

    # Sort modalities by length
    asort = argsort(lengths)
    modalities = [modalities[i] for i in asort]
    lengths = [lengths[i] for i in asort]
    modes = [modes[i] for i in asort]

    return plot_png(spec, modalities, nmodes, lengths)


# plot png helpers
def argsort(arr: List[Any]) -> List[int]:
    return sorted(range(len(arr)), key=arr.__getitem__)


def total_length(libspec) -> int:
    return sum(leaf.min_len for leaf in libspec.get_leaves())


def ensure_axes_list(ax_or_axes):
    if isinstance(ax_or_axes, np.ndarray):
        return list(ax_or_axes.ravel())
    return [ax_or_axes]


def plot_libspec(
    ax, libspec, region_height=1.0, label_fontsize=11
) -> Tuple[List[str], float]:
    """Draw library regions; return list of region types and max x reached."""
    leaves = libspec.get_leaves()
    y, x, h = 0.0, 0.0, float(region_height)
    region_types = []
    for node in leaves:
        rtype = node.region_type.lower()
        region_types.append(rtype)
        length = float(node.min_len)

        rect = Rectangle((x, y), length, h, color=REGION_TYPE_COLORS[rtype], ec="black")
        ax.add_patch(rect)

        # center length text
        ax.text(
            x + length / 2.0,
            y + h / 2.0,
            f"{int(length)}",
            ha="center",
            va="center",
            fontsize=label_fontsize,
            color="k",
            clip_on=False,
        )
        x += length
    return region_types, x


def plot_seqspec(
    ax, libspec, reads, region_height=1.0, arrow_scale=44, text_size=12
) -> Tuple[float, float]:
    """Draw reads; return global min_x and max_x touched by arrows."""
    leaves = libspec.get_leaves()
    cuts = project_regions_to_coordinates(leaves)
    # map region_id -> index once
    idx_by_region = {leaf.region_id: i for i, leaf in enumerate(leaves)}

    y_pos = region_height + 1.0  # a bit above the bar
    y_neg = -1.0  # a bit below the bar

    x_min, x_max = math.inf, -math.inf

    for rd in reads:
        pidx = idx_by_region[rd.primer_id]
        primer_start = float(cuts[pidx].start)
        primer_stop = float(cuts[pidx].stop)
        rlen = float(rd.min_len)

        if rd.strand == "pos":
            xt, xh, y, color = primer_stop, primer_stop + rlen, y_pos, "green"
        else:
            xt, xh, y, color = primer_start, primer_start - rlen, y_neg, "red"

        # record extents to set xlim later
        x_min = min(x_min, xt, xh)
        x_max = max(x_max, xt, xh)

        arrow = FancyArrowPatch(
            (xt, y),
            (xh, y),
            arrowstyle="simple",
            mutation_scale=arrow_scale,
            facecolor=color,
            edgecolor="k",
            linewidth=1.0,
            clip_on=False,
            zorder=5,
        )
        ax.add_patch(arrow)
        # Place text so it ends at the tail (outside the arrow)
        if rd.strand == "pos":
            ax.text(
                xt,
                y,
                rd.read_id,
                ha="right",
                va="center",
                fontsize=text_size,
                color="k",
                clip_on=False,
                zorder=6,
            )
        else:  # reverse
            ax.text(
                xt,
                y,
                rd.read_id,
                ha="left",
                va="center",
                fontsize=text_size,
                color="k",
                clip_on=False,
                zorder=6,
            )
    # If there were no reads, keep limits reasonable
    if x_min is math.inf:
        x_min, x_max = 0.0, 0.0
    return x_min, x_max


def plot_png(spec: Assay, modalities: List[str], nmodes: int, lengths: List[int]):
    """Create PNG plot of sequence specification.

    Args:
        spec: The assay ID.
        modalities: List of modalities.
        modes: List of mode specifications.
        nmodes: Number of modes.
        lengths: List of lengths.

    Returns:
        The matplotlib figure.
    """

    fig_h = max(1.6 * nmodes, 2.5)

    # slightly larger base font when there are few rows
    base_fs = 13 if nmodes <= 2 else 12
    plt.rcParams.update({"font.size": base_fs})

    fig, axes = plt.subplots(
        nrows=nmodes, figsize=(12, fig_h), sharex=True, constrained_layout=True
    )
    axes = ensure_axes_list(axes)

    fig.suptitle(spec.assay_id, y=0.995)

    all_region_types = set()
    global_xmin, global_xmax = math.inf, -math.inf
    region_height = 1.0

    seqspec_reads = spec.sequence_spec

    for idx, (m, ax) in enumerate(zip(modalities, axes)):
        libspec = spec.get_libspec(m)
        reads = [r for r in seqspec_reads if r.modality == m]

        rtypes, lib_xmax = plot_libspec(
            ax, libspec, region_height=region_height, label_fontsize=base_fs - 1
        )
        all_region_types.update(rtypes)

        rmin, rmax = plot_seqspec(
            ax,
            libspec,
            reads,
            region_height=region_height,
            arrow_scale=44,
            text_size=base_fs,
        )
        xmin = min(0.0, rmin)
        xmax = max(float(lib_xmax), rmax)
        global_xmin, global_xmax = min(global_xmin, xmin), max(global_xmax, xmax)

        # cosmetics
        ax.margins(x=0.02, y=0.35)  # add breathing room so arrows/text aren’t clipped
        for spine in ("right", "top", "left", "bottom"):
            ax.spines[spine].set_visible(False)
        ax.set_yticks([])
        ax.xaxis.set_visible(False)
        ax.set_ylabel(m, rotation=0, fontsize=base_fs + 5, ha="right", va="center")

    # unified x-limits with a bit of pad
    pad = max(
        5.0,
        0.02
        * (
            global_xmax - global_xmin
            if math.isfinite(global_xmax - global_xmin)
            else 100
        ),
    )
    if not math.isfinite(global_xmin):  # no reads at all edge-case
        global_xmin, global_xmax = 0.0, max(lengths)

    axes[-1].set_xlim(global_xmin - pad, global_xmax + pad)
    axes[-1].xaxis.set_visible(True)
    axes[-1].spines["bottom"].set_visible(True)
    axes[-1].minorticks_on()
    axes[-1].set_xlabel("# nucleotides")

    # legend outside, no frame
    handles = [
        mpatches.Patch(color=REGION_TYPE_COLORS[t], label=t)
        for t in sorted(all_region_types)
    ]
    if handles:
        fig.legend(
            handles=handles, loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=True
        )

    return fig

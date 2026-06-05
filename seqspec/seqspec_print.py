"""Print module for seqspec CLI.

This module provides functionality to print sequence and/or library structure
in various formats (ascii, png, html).
"""

import os
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path
from typing import Any, List

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import newick
import numpy as np
from matplotlib.patches import FancyArrowPatch, Rectangle

from seqspec.Assay import Assay
from seqspec.Region import complement_sequence
from seqspec.seqspec_print_html import build_seqspec_view_data, print_seqspec_html
from seqspec.seqspec_print_utils import libseq
from seqspec.utils import is_remote_source, load_spec

STATIC_RENDER_FORMATS = {"seqspec-png", "seqspec-pdf"}
LABEL_MODES = ("name", "region_id", "length", "name+length", "none")
SEQUENCE_TYPE_COLORS = {
    "fixed": "#e2e5e9",
    "onlist": "#bbf7d0",
    "random": "#bfdbfe",
}
SEQUENCE_TYPE_STROKES = {
    "fixed": "#b0b5bc",
    "onlist": "#4ade80",
    "random": "#60a5fa",
}
READ_COLORS = ["#1e40af", "#059669", "#d97706", "#dc2626", "#7c3aed"]


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
seqspec print -o spec.pdf -f seqspec-pdf spec.yaml # Print the library structure as a pdf
---
        """,
        help="Display the sequence and/or library structure from seqspec file",
        formatter_class=RawTextHelpFormatter,
    )

    subparser.add_argument(
        "yaml", type=str, help="Path or URL to sequencing specification YAML"
    )
    subparser.add_argument(
        "-o",
        "--output",
        metavar="OUT",
        type=Path,
        help="Path to output file",
        default=None,
    )

    format_choices = [
        "library-ascii",
        "seqspec-html",
        "seqspec-png",
        "seqspec-pdf",
        "seqspec-ascii",
    ]
    subparser.add_argument(
        "-f",
        "--format",
        metavar="FORMAT",
        help=f"Format ({', '.join(format_choices)}), default: library-ascii",
        type=str,
        default="library-ascii",
        choices=format_choices,
    )
    subparser.add_argument(
        "--auth-profile",
        metavar="PROFILE",
        help="Authentication profile for remote spec access",
        type=str,
        default=os.environ.get("SEQSPEC_AUTH_PROFILE"),
    )
    subparser.add_argument(
        "--label",
        metavar="LABEL",
        help=(
            "Region labels for PNG/PDF output "
            f"({', '.join(LABEL_MODES)}), default: name"
        ),
        type=str,
        default="name",
        choices=LABEL_MODES,
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
    if not is_remote_source(args.yaml) and not Path(args.yaml).exists():
        parser.error(f"Input file does not exist: {args.yaml}")

    if args.output and Path(args.output).exists() and not Path(args.output).is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")
    if args.label != "name" and args.format not in STATIC_RENDER_FORMATS:
        parser.error("--label is only supported with seqspec-png and seqspec-pdf")


def run_print(parser: ArgumentParser, args: Namespace) -> None:
    """Run the print command.

    Args:
        parser: The argument parser.
        args: The parsed arguments.
    """

    validate_print_args(parser, args)

    spec = load_spec(args.yaml, auth_profile=args.auth_profile)
    result = seqspec_print(spec, args.format, label=args.label)

    if args.output:
        if args.format in STATIC_RENDER_FORMATS:
            result.savefig(args.output, dpi=300, bbox_inches="tight")
        else:
            with open(args.output, "w") as f:
                print(result, file=f)
    else:
        if args.format in STATIC_RENDER_FORMATS:
            plt.show()
        else:
            print(result)


def seqspec_print(spec: Assay, fmt: str, label: str = "name"):
    """Print sequence specification in the specified format.

    Args:
        spec: The seqspec specification to print
        fmt: The format to print in (library-ascii, seqspec-html, seqspec-png, seqspec-pdf, seqspec-ascii)
        label: Region label mode for static image formats

    Returns:
        The formatted output (string or matplotlib figure)

    Raises:
        ValueError: If format is not supported
    """
    if label not in LABEL_MODES:
        raise ValueError(
            f"Unsupported label: {label}. Must be one of {list(LABEL_MODES)}"
        )

    if fmt == "seqspec-png":
        return print_seqspec_png(spec, label=label)
    if fmt == "seqspec-pdf":
        return print_seqspec_png(spec, label=label)

    format_to_function = {
        "library-ascii": print_library_ascii,
        "seqspec-html": print_seqspec_html,
        "seqspec-ascii": print_seqspec_ascii,
    }
    if fmt not in format_to_function:
        raise ValueError(
            "Unsupported format: "
            f"{fmt}. Must be one of {list(format_to_function.keys()) + sorted(STATIC_RENDER_FORMATS)}"
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


def print_seqspec_png(spec: Assay, label: str = "name"):
    """Print sequence specification as PNG.

    Args:
        spec: The seqspec specification to print.
        label: Region label mode.

    Returns:
        The matplotlib figure.
    """
    return plot_png(build_seqspec_view_data(spec), label=label)


def ensure_axes_list(ax_or_axes):
    if isinstance(ax_or_axes, np.ndarray):
        return list(ax_or_axes.ravel())
    return [ax_or_axes]


def region_label(region: dict[str, Any], label: str) -> str:
    if label == "none":
        return ""
    if label == "name":
        return str(region["name"])
    if label == "region_id":
        return str(region["region_id"])
    if label == "length":
        return str(region["len"])
    if label == "name+length":
        return f"{region['name']} {region['len']}"
    raise ValueError(f"Unsupported label: {label}")


def is_short_region(region: dict[str, Any], text: str) -> bool:
    """Return true when a region label needs an external callout."""
    if not text:
        return False
    length = max(float(region["bp_end"] - region["bp_start"]), 0.0)
    return length < max(14.0, len(text) * 2.6)


def sequence_type_color(sequence_type: str) -> str:
    return SEQUENCE_TYPE_COLORS.get(sequence_type, SEQUENCE_TYPE_COLORS["fixed"])


def sequence_type_stroke(sequence_type: str) -> str:
    return SEQUENCE_TYPE_STROKES.get(sequence_type, SEQUENCE_TYPE_STROKES["fixed"])


def estimate_label_width_bp(text: str) -> float:
    """Estimate static label width in nucleotide coordinates."""
    return max(4.0, len(text) * 2.6)


def choose_callout_lane(
    center: float, text: str, lane_ends: list[float]
) -> tuple[int, float]:
    text_x = center + 2.6
    label_end = text_x + estimate_label_width_bp(text)
    gap = 2.0

    for lane, lane_end in enumerate(lane_ends):
        if text_x >= lane_end + gap:
            lane_ends[lane] = label_end
            return lane, text_x

    lane = min(range(len(lane_ends)), key=lane_ends.__getitem__)
    text_x = lane_ends[lane] + gap
    lane_ends[lane] = text_x + estimate_label_width_bp(text)
    return lane, text_x


def draw_region_labels(ax, regions, label_mode, bar_y, bar_h, fontsize):
    callout_count = 0
    callout_lanes = {
        "above": [-float("inf"), -float("inf"), -float("inf")],
        "below": [-float("inf"), -float("inf"), -float("inf")],
    }
    for region in regions:
        text = region_label(region, label_mode)
        if not text:
            continue

        start = float(region["bp_start"])
        end = float(region["bp_end"])
        center = start + (end - start) / 2.0

        if is_short_region(region, text):
            side = "below" if callout_count % 2 == 0 else "above"
            lane, text_x = choose_callout_lane(center, text, callout_lanes[side])
            if side == "above":
                anchor_y = bar_y + bar_h
                text_y = bar_y + bar_h + 0.34 + 0.30 * lane
            else:
                anchor_y = bar_y
                text_y = bar_y - 0.48 - 0.34 * lane
            label_left = text_x - 0.65
            ax.plot(
                [center, center],
                [anchor_y, text_y],
                color="#848a92",
                linewidth=0.7,
                zorder=7,
                clip_on=False,
            )
            ax.plot(
                [center, label_left],
                [text_y, text_y],
                color="#848a92",
                linewidth=0.7,
                zorder=7,
                clip_on=False,
            )
            ax.text(
                text_x,
                text_y,
                text,
                ha="left",
                va="center",
                fontsize=fontsize,
                fontfamily="monospace",
                color="#4a5058",
                clip_on=False,
                zorder=8,
            )
            callout_count += 1
        else:
            ax.text(
                center,
                bar_y + bar_h + 0.16,
                text,
                rotation=40,
                ha="left",
                va="bottom",
                fontsize=fontsize,
                fontfamily="monospace",
                color="#4a5058",
                clip_on=False,
                zorder=8,
            )


def draw_regions(
    ax, modality: dict[str, Any], label_mode: str, fontsize: int
) -> set[str]:
    bar_y = 0.0
    bar_h = 0.22
    group_gap = 0.16
    group_h = 0.08
    region_types = set()

    group_regions = [r for r in modality["region_nodes"] if not r["is_leaf"]]
    max_depth = max((r["depth"] for r in group_regions), default=-1)
    group_top = bar_y + bar_h + 0.42 + max_depth * group_gap

    for region in group_regions:
        start = float(region["bp_start"])
        width = max(float(region["bp_end"] - region["bp_start"]), 0.001)
        y = group_top - region["depth"] * group_gap
        rect = Rectangle(
            (start, y),
            width,
            group_h,
            facecolor="white",
            edgecolor="#848a92",
            linewidth=0.85,
            zorder=3,
        )
        ax.add_patch(rect)
        if width > 42:
            ax.text(
                start + 1,
                y + group_h + 0.02,
                region["name"],
                ha="left",
                va="bottom",
                fontsize=fontsize - 2,
                fontfamily="monospace",
                color="#848a92",
                clip_on=False,
            )

    for region in modality["regions"]:
        sequence_type = str(region["sequence_type"])
        region_types.add(sequence_type)
        start = float(region["bp_start"])
        width = max(float(region["bp_end"] - region["bp_start"]), 0.001)
        rect = Rectangle(
            (start, bar_y),
            width,
            bar_h,
            facecolor=sequence_type_color(sequence_type),
            edgecolor=sequence_type_stroke(sequence_type),
            linewidth=0.8,
            zorder=4,
        )
        ax.add_patch(rect)

    draw_region_labels(ax, modality["regions"], label_mode, bar_y, bar_h, fontsize - 1)
    return region_types


def draw_reads(ax, modality: dict[str, Any], fontsize: int) -> tuple[float, float]:
    pos_reads = [read for read in modality["reads"] if read["strand"] == "pos"]
    neg_reads = [read for read in modality["reads"] if read["strand"] == "neg"]
    x_min, x_max = 0.0, float(modality["total_bp"])

    def draw_read(read, y, color_index, above):
        nonlocal x_min, x_max
        start = float(read["start"])
        end = float(read["end"])
        x_min = min(x_min, start, end)
        x_max = max(x_max, start, end)
        color = READ_COLORS[color_index % len(READ_COLORS)]
        arrow_start = start if above else end
        arrow_end = end if above else start
        arrow = FancyArrowPatch(
            (arrow_start, y),
            (arrow_end, y),
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.6,
            color=color,
            clip_on=False,
            zorder=6,
        )
        ax.add_patch(arrow)
        anchor_x = start if above else end
        anchor_y = 0.0 if above else 0.22
        ax.plot(
            [anchor_x, anchor_x],
            [anchor_y, y],
            color=color,
            linewidth=0.8,
            linestyle=(0, (2, 2)),
            alpha=0.45,
            zorder=5,
        )
        if above:
            ax.text(
                start + 1,
                y + 0.06,
                read["label"] or read["read_id"],
                ha="left",
                va="bottom",
                fontsize=fontsize - 1,
                fontfamily="monospace",
                color=color,
                clip_on=False,
                zorder=7,
            )
        else:
            ax.text(
                end - 1,
                y - 0.06,
                read["label"] or read["read_id"],
                ha="right",
                va="top",
                fontsize=fontsize - 1,
                fontfamily="monospace",
                color=color,
                clip_on=False,
                zorder=7,
            )

    y = 1.38
    for index, read in enumerate(pos_reads):
        draw_read(read, y, index, True)
        y += 0.36

    y = -1.62
    for index, read in enumerate(neg_reads):
        draw_read(read, y, len(pos_reads) + index, False)
        y -= 0.36

    return x_min, x_max


def plot_png(payload: dict[str, Any], label: str = "name"):
    """Create PNG plot of sequence specification.

    Args:
        payload: Shared seqspec view model used by the HTML renderer.
        label: Region label mode.

    Returns:
        The matplotlib figure.
    """
    modalities = payload["modalities"]
    nmodes = len(modalities)
    fig_h = max(1.8 * nmodes, 2.4)

    base_fs = 13 if nmodes <= 2 else 12
    plt.rcParams.update({"font.size": base_fs})

    fig, axes = plt.subplots(
        nrows=nmodes, figsize=(12, fig_h), sharex=True, constrained_layout=True
    )
    axes = ensure_axes_list(axes)

    fig.suptitle(payload["assay_id"], y=0.995, fontfamily="monospace")

    all_sequence_types = set()
    global_xmin = 0.0
    global_xmax = max((float(m["total_bp"]) for m in modalities), default=1.0)

    for modality, ax in zip(modalities, axes):
        all_sequence_types.update(draw_regions(ax, modality, label, base_fs))
        xmin, xmax = draw_reads(ax, modality, base_fs)
        global_xmin = min(global_xmin, xmin)
        global_xmax = max(global_xmax, xmax)

        ax.set_ylim(-2.35, 2.05)
        for spine in ("right", "top", "left", "bottom"):
            ax.spines[spine].set_visible(False)
        ax.set_yticks([])
        ax.xaxis.set_visible(False)
        ax.set_ylabel(
            modality["modality"],
            rotation=0,
            fontsize=base_fs + 5,
            ha="right",
            va="center",
            fontfamily="monospace",
        )

    pad = max(5.0, 0.02 * (global_xmax - global_xmin))

    axes[-1].set_xlim(global_xmin - pad, global_xmax + pad)
    axes[-1].xaxis.set_visible(True)
    axes[-1].spines["bottom"].set_visible(True)
    axes[-1].minorticks_on()
    axes[-1].set_xlabel("# nucleotides")

    handles = [
        mpatches.Patch(
            facecolor=sequence_type_color(t),
            edgecolor=sequence_type_stroke(t),
            label=t,
        )
        for t in sorted(all_sequence_types)
    ]
    if handles:
        fig.legend(
            handles=handles, loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=True
        )

    return fig

"""Print module for seqspec CLI.

This module provides functionality to print sequence and/or library structure
in various formats (ascii, png, html).
"""

from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path
from typing import Any, List

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import newick
from matplotlib.patches import Rectangle

from seqspec.Assay import Assay
from seqspec.Region import complement_sequence
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

    if args.format == "seqspec-png" and args.output is None:
        parser.error("Output file required for png format")


def run_print(parser: ArgumentParser, args: Namespace) -> None:
    """Run the print command.

    Args:
        parser: The argument parser.
        args: The parsed arguments.
    """

    validate_print_args(parser, args)

    spec = load_spec(args.yaml)
    result = seqspec_print(spec, args.format)

    if args.format == "seqspec-png":
        result.savefig(args.output, dpi=300, bbox_inches="tight")
    elif args.output:
        with open(args.output, "w") as f:
            print(result, file=f)
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

    return plot_png(spec.assay_id, modalities, modes, nmodes, lengths)


def argsort(arr: List[Any]) -> List[int]:
    """Get indices that would sort an array.

    Args:
        arr: The array to sort.

    Returns:
        List of indices that would sort the array.
    """
    return sorted(range(len(arr)), key=arr.__getitem__)


def plot_png(
    assay: str, modalities: List[str], modes: List[Any], nmodes: int, lengths: List[int]
):
    """Create PNG plot of sequence specification.

    Args:
        assay: The assay ID.
        modalities: List of modalities.
        modes: List of mode specifications.
        nmodes: Number of modes.
        lengths: List of lengths.

    Returns:
        The matplotlib figure.
    """
    fsize = 15
    plt.rcParams.update({"font.size": fsize})

    fig, _ = plt.subplots(figsize=(10, 1 * nmodes), nrows=nmodes)
    title_offset = 0.98 if nmodes > 1 else 1.2
    fig.suptitle(assay, y=title_offset)

    rts = []
    for m, ax in zip(modes, fig.get_axes()):
        # Get leaves
        leaves = m.get_leaves()

        # Setup plotting variables
        y = 0
        x = 0
        height = 1

        for idx, node in enumerate(leaves):
            # Region type
            rtype = node.region_type.lower()
            rts.append(rtype)

            # Get region properties
            length = node.min_len
            label = f"{length}"

            # Setup rectangle for the region
            rectangle = Rectangle(
                (x, y), length, height, color=REGION_TYPE_COLORS[rtype], ec="black"
            )

            # Write length in the rectangle
            ax.text(
                x + length / 2,
                y + height / 2,
                label,
                horizontalalignment="center",
                verticalalignment="center",
            )
            ax.add_patch(rectangle)

            # Add length to x for next region
            x += length

        ax.autoscale()
        ax.set(**{"xlim": (0, max(lengths)), "ylim": (0, 1)})

        # Hide the spines
        for spine in ["right", "top", "left", "bottom"]:
            ax.spines[spine].set_visible(False)
        # Hide the axis and ticks and labels
        ax.xaxis.set_visible(False)
        ax.set_yticklabels([])
        ax.set_yticks([])

        # Label the modality on the ylabel
        ax.set_ylabel(m.region_type, rotation=0, fontsize=20, ha="right", va="center")

    # Adjust the xaxis for the last modality to show the length
    ax.xaxis.set_visible(True)
    ax.spines["bottom"].set_visible(True)
    ax.minorticks_on()

    ax.set(
        **{
            "xlabel": "# nucleotides",
        }
    )

    # Setup the figure legend
    handles = []
    for t in sorted(set(rts)):
        handles.append(mpatches.Patch(color=REGION_TYPE_COLORS[t], label=t))
    fig.legend(handles=handles, loc="center", bbox_to_anchor=(1.1, 0.55))

    return fig

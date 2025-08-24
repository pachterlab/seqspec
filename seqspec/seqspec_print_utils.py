"""Utility functions for printing seqspec files.

This module contains shared functionality used by both seqspec_print.py and seqspec_print_html.py.
"""

from typing import List, Tuple

from seqspec.Assay import Assay
from seqspec.Region import complement_sequence, project_regions_to_coordinates


def libseq(spec: Assay, modality: str) -> Tuple[List[str], List[str]]:
    """Get library sequence parts for a specific modality.

    Args:
        spec: The seqspec specification.
        modality: The modality to get parts for.

    Returns:
        Tuple of (positive strand parts, negative strand parts).
    """
    libspec = spec.get_libspec(modality)
    seqspec = spec.get_seqspec(modality)

    p = []
    n = []

    for idx, read in enumerate(seqspec, 1):
        read_len = read.max_len
        read_id = read.read_id
        primer_id = read.primer_id

        leaves = libspec.get_leaves_with_region_id(primer_id)
        primer_idx = [
            idx for idx, leaf in enumerate(leaves) if leaf.region_id == primer_id
        ][0]

        cuts = project_regions_to_coordinates(leaves)
        # TODO: contract the cuts so they are viewable

        primer_pos = cuts[primer_idx]
        # print(cuts)

        if read.strand == "pos":
            # start position of the arrow (where primer ends)
            wsl = primer_pos.stop - 1
            ws = wsl * " "

            # length of the arrow
            arrowl = read_len - 1
            arrow = arrowl * "-"

            p.append(f"{ws}|{arrow}>({idx}) {read_id}")
        elif read.strand == "neg":
            wsl = primer_pos.start - read_len
            ws = wsl * " "

            arrowl = read_len - 1
            arrow = arrowl * "-"

            n.append(f"{ws}<{arrow}|({idx}) {read_id}")

    return (p, n)


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

"""Diff module for seqspec.

This module provides functionality to compare two seqspec files and identify differences.
"""

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import List

from seqspec.Assay import Assay
from seqspec.Region import Region
from seqspec.utils import load_spec


def setup_diff_args(parser) -> ArgumentParser:
    """Create and configure the diff command subparser."""
    subparser = parser.add_parser(
        "diff",
        description="""
Compare two seqspec files and identify differences.

Examples:
seqspec diff spec1.yaml spec2.yaml                    # Compare two specs and print differences
seqspec diff spec1.yaml spec2.yaml -o diff.txt        # Compare specs and save differences to file
---
""",
        help="Compare two seqspec files and identify differences",
    )
    subparser.add_argument(
        "yamlA", help="First sequencing specification yaml file", type=str
    )
    subparser.add_argument(
        "yamlB", help="Second sequencing specification yaml file", type=str
    )
    subparser.add_argument(
        "-o",
        "--output",
        metavar="OUT",
        help="Path to output file",
        type=Path,
        default=None,
    )
    return subparser


def validate_diff_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the diff command arguments."""
    if not Path(args.yamlA).exists():
        parser.error(f"Input file A does not exist: {args.yamlA}")
    if not Path(args.yamlB).exists():
        parser.error(f"Input file B does not exist: {args.yamlB}")
    if args.output and args.output.exists() and not args.output.is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")


def run_diff(parser: ArgumentParser, args: Namespace) -> None:
    """Run the diff command."""
    validate_diff_args(parser, args)

    spec_a = load_spec(args.yamlA)
    spec_b = load_spec(args.yamlB)

    differences = compare_specs(spec_a, spec_b)

    if args.output:
        args.output.write_text(differences)
    else:
        print(differences)


def compare_specs(spec_a: Assay, spec_b: Assay) -> str:
    """Compare two specs and return a string describing their differences."""
    differences = []

    # Compare modalities
    modalities_a = set(spec_a.modalities)
    modalities_b = set(spec_b.modalities)

    if modalities_a != modalities_b:
        differences.append("Modalities differ:")
        differences.append(f"  Spec A: {', '.join(sorted(modalities_a))}")
        differences.append(f"  Spec B: {', '.join(sorted(modalities_b))}")

    # Compare common modalities
    common_modalities = modalities_a.intersection(modalities_b)
    for modality in common_modalities:
        regions_a = spec_a.get_libspec(modality).get_leaves()
        regions_b = spec_b.get_libspec(modality).get_leaves()

        region_diffs = compare_regions(regions_a, regions_b)
        if region_diffs:
            differences.append(f"\nModality '{modality}' differences:")
            differences.extend(region_diffs)

    return "\n".join(differences) if differences else "No differences found"


def compare_regions(regions_a: List[Region], regions_b: List[Region]) -> List[str]:
    """Compare two lists of regions and return a list of differences."""
    differences = []

    # Create lookup dictionaries
    regions_a_dict = {r.region_id: r for r in regions_a}
    regions_b_dict = {r.region_id: r for r in regions_b}

    # Find regions unique to each spec
    unique_to_a = set(regions_a_dict.keys()) - set(regions_b_dict.keys())
    unique_to_b = set(regions_b_dict.keys()) - set(regions_a_dict.keys())

    if unique_to_a:
        differences.append("  Regions only in spec A:")
        for region_id in sorted(unique_to_a):
            differences.append(f"    - {region_id}")

    if unique_to_b:
        differences.append("  Regions only in spec B:")
        for region_id in sorted(unique_to_b):
            differences.append(f"    - {region_id}")

    # Compare common regions
    common_regions = set(regions_a_dict.keys()).intersection(set(regions_b_dict.keys()))
    for region_id in sorted(common_regions):
        region_a = regions_a_dict[region_id]
        region_b = regions_b_dict[region_id]

        region_diffs = diff_regions(region_a, region_b)
        if region_diffs:
            differences.append(f"  Region '{region_id}' differences:")
            differences.extend(f"    - {diff}" for diff in region_diffs)

    return differences


def diff_regions(region_a: Region, region_b: Region) -> List[str]:
    """Compare two regions and return a list of differences."""
    differences = []

    # Compare basic properties
    if region_a.region_type != region_b.region_type:
        differences.append(
            f"region_type: {region_a.region_type} != {region_b.region_type}"
        )
    if region_a.name != region_b.name:
        differences.append(f"name: {region_a.name} != {region_b.name}")
    if region_a.sequence_type != region_b.sequence_type:
        differences.append(
            f"sequence_type: {region_a.sequence_type} != {region_b.sequence_type}"
        )
    if region_a.sequence != region_b.sequence:
        differences.append(f"sequence: {region_a.sequence} != {region_b.sequence}")
    if region_a.min_len != region_b.min_len:
        differences.append(f"min_len: {region_a.min_len} != {region_b.min_len}")
    if region_a.max_len != region_b.max_len:
        differences.append(f"max_len: {region_a.max_len} != {region_b.max_len}")

    return differences

"""Convert module for seqspec CLI.

This module provides functionality to convert between different formats (seqspec, genbank, token).
"""
from pathlib import Path
from argparse import ArgumentParser, RawTextHelpFormatter, Namespace
import json
import numpy as np
from typing import Dict, List, Tuple
import os

from seqspec.utils import load_genbank, load_spec
from seqspec.Region import Region
from seqspec.Assay import Assay


# Load schema and constants
schema_fn = os.path.join(os.path.dirname(__file__), "schema/seqspec.schema.json")
with open(schema_fn, "r") as f:
    schema = json.load(f)
REGION_TYPES = schema["$defs"]["region"]["properties"]["region_type"]["enum"]
MODALITIES = schema["properties"]["modalities"]["items"]["enum"]
SEQUENCE_TYPES = schema["$defs"]["region"]["properties"]["sequence_type"]["enum"]


def setup_convert_args(parser) -> ArgumentParser:
    """Create and configure the convert command subparser."""
    subparser = parser.add_parser(
        "convert",
        description="""
Convert between different formats (seqspec, genbank, token).

Examples:
seqspec convert -ifmt seqspec -ofmt token spec.yaml -o output_dir  # Convert seqspec to token format
seqspec convert -ifmt genbank -ofmt seqspec input.gb -o spec.yaml  # Convert genbank to seqspec
---
""",
        help="Convert between different formats",
        formatter_class=RawTextHelpFormatter,
    )
    choices = ["genbank", "seqspec", "token"]
    subparser.add_argument(
        "-ifmt",
        "--input-format",
        help="Input format",
        type=str,
        default="seqspec",
        choices=choices,
    )
    subparser.add_argument(
        "-ofmt",
        "--output-format",
        help="Output format",
        type=str,
        default="token",
        choices=choices,
    )
    subparser.add_argument(
        "-o",
        "--output",
        metavar="OUT",
        help="Path to output file or directory",
        type=Path,
        default=None,
        required=False,
    )
    subparser.add_argument(
        "input_file",
        metavar="IN",
        help="Path to input file",
        type=Path,
    )
    return subparser


def validate_convert_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the convert command arguments."""
    if not Path(args.input_file).exists():
        parser.error(f"Input file does not exist: {args.input_file}")

    if args.output and Path(args.output).exists():
        if args.output_format == "token":
            if not Path(args.output).is_dir():
                parser.error(
                    f"Output path exists but is not a directory: {args.output}"
                )
        else:
            if not Path(args.output).is_file():
                parser.error(f"Output path exists but is not a file: {args.output}")


def run_convert(parser: ArgumentParser, args: Namespace) -> None:
    """Run the convert command."""
    validate_convert_args(parser, args)

    CONVERT = {
        ("genbank", "seqspec"): gb_to_seqspec,
        ("seqspec", "token"): seqspec_to_token,
    }

    file = load_input_file(args.input_file, args.input_format)
    result = CONVERT[(args.input_format, args.output_format)](file)

    if args.output:
        if args.output_format == "token":
            save_tokenized_spec(*result, str(args.output))  # noqa
        else:
            # Handle other output formats here
            pass
    else:
        return result


def load_input_file(fn: Path, ifmt: str):
    """Load input file based on format."""
    LOAD = {
        "genbank": load_genbank,
        "seqspec": load_spec,
        # "token": load_token,
    }
    return LOAD[ifmt](fn)


def get_feature_names() -> List[str]:
    """Generate ordered list of column names"""
    features = []

    # Modality one-hot features
    features.extend([f"modality_{mod}" for mod in MODALITIES])

    # Region type one-hot features
    features.extend([f"region_{rt}" for rt in REGION_TYPES])

    # Sequence type one-hot features
    features.extend([f"seq_{st}" for st in SEQUENCE_TYPES])

    # Numerical features
    features.extend(["min_len", "max_len", "position"])

    return features


def save_tokenized_spec(
    matrix: np.ndarray, row_identifiers: List[Tuple[str, str, str]], output_path: str
):
    """
    Save tokenized spec output to three files:
    - spec.npy: The matrix data
    - rows.txt: Tab-separated list of (spec_id, modality, region_type)
    - cols.txt: List of column names

    Args:
        matrix: The tokenized matrix from tokenize_specs
        row_identifiers: List of (spec_id, modality, region_type) tuples
        output_path: Path to save the output (directory)
    """
    # Create output directory if needed
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save matrix
    np.save(output_dir / "spec.npy", matrix)

    # Save row identifiers (tab-separated)
    with open(output_dir / "rows.txt", "w") as f:
        for spec_id, modality, region_type in row_identifiers:
            f.write(f"{spec_id}\t{modality}\t{region_type}\n")

    # Save column names
    feature_names = get_feature_names()
    with open(output_dir / "cols.txt", "w") as f:
        for feature in feature_names:
            f.write(f"{feature}\n")


def seqspec_to_token(spec):
    # for each modalitiy, make a dictionary of regions
    specs_regions = {}
    modalities = spec.list_modalities()
    for modality in modalities:
        regions = [i.to_dict() for i in spec.get_libspec(modality).get_leaves()]
        specs_regions[modality] = regions

    # Convert to tokenized matrix
    return tokenize_specs({spec.assay_id: specs_regions})


def tokenize_specs(
    specs_regions: Dict[str, Dict[str, List[Dict]]]
) -> Tuple[np.ndarray, List[Tuple[str, str, str]]]:
    """
    Convert specs into a single matrix where each row represents a complete region specification

    Args:
        specs_regions: Dict[spec_id -> Dict[modality -> List[region_dict]]]

    Returns:
        - Matrix where each row is [modality_onehot, region_type_onehot, sequence_type_onehot, min_len, max_len, position]
        - List of (spec_id, modality, region_type) identifying each row
    """
    # Calculate feature dimensions
    n_modality_features = len(MODALITIES)
    n_region_type_features = len(REGION_TYPES)
    n_sequence_type_features = len(SEQUENCE_TYPES)

    # Total features = one-hot encodings + numerical features + position
    total_features = (
        n_modality_features  # modality one-hot
        + n_region_type_features  # region_type one-hot
        + n_sequence_type_features  # sequence_type one-hot
        + 2  # min_len, max_len
        + 1  # position in region list (1-based)
    )

    # features = get_feature_names()

    rows = []  # Will hold our feature vectors
    row_identifiers = []  # Will hold (spec_id, modality, region_type) tuples

    for spec_id, modality_regions in specs_regions.items():
        for modality, regions in modality_regions.items():
            # Enumerate regions to get position (1-based)
            for position, region in enumerate(regions, start=1):
                # Create feature vector for this region
                feature_vector = np.zeros(total_features).astype(int)
                current_idx = 0

                # Add modality one-hot
                modality_idx = MODALITIES.index(modality)
                feature_vector[modality_idx] = 1
                current_idx += n_modality_features

                # Add region_type one-hot
                region_type_idx = REGION_TYPES.index(region["region_type"])
                feature_vector[current_idx + region_type_idx] = 1
                current_idx += n_region_type_features

                # Add sequence_type one-hot
                sequence_type_idx = SEQUENCE_TYPES.index(region["sequence_type"])
                feature_vector[current_idx + sequence_type_idx] = 1
                current_idx += n_sequence_type_features

                # Add lengths
                feature_vector[current_idx] = region["min_len"]
                feature_vector[current_idx + 1] = region["max_len"]
                current_idx += 2

                # Add position
                feature_vector[current_idx] = position

                # Store feature vector and identifier
                rows.append(feature_vector)
                row_identifiers.append((spec_id, modality, region["region_type"]))

    return np.array(rows), row_identifiers


def gb_to_seqspec(gb):
    ex = gb_to_list(gb)
    nested_json = nest_intervals(ex)
    filled_regions = fill_gaps(gb.sequence, nested_json)
    regions = convert(filled_regions)
    reads = []
    spec = Assay(
        "genbank",
        "illumina",
        "genbank thing",
        "doi",
        "date",
        ["source"],
        "description",
        "",
        "",
        "",
        "",
        reads,
        regions,
    )
    return spec


def gb_to_list(gb):
    feat = []
    label = "source"
    for f in gb.features:
        id = f.key

        if "complement" in f.location:
            start, stop = tuple(map(int, f.location[11:-1].split("..")))
        else:
            start, stop = tuple(map(int, f.location.split("..")))

        # convert to 0-index
        start -= 1
        length = stop - start
        seq = gb.sequence[start:stop]

        for q in f.qualifiers:
            if q.key == "/label=":
                label = q.value
                break
        feat.append(
            {
                "id": id,
                "label": label,
                "start": start,
                "stop": stop,
                "length": length,
                "seq": seq,
            }
        )
    return feat


def nest_intervals(intervals):
    def nest(start_index, end_limit):
        nested = []

        i = start_index
        while i < len(intervals) and intervals[i]["start"] < end_limit:
            current_interval = intervals[i]
            child, next_index = nest(i + 1, current_interval["stop"])
            interval_obj = {
                "id": current_interval["id"],
                "label": current_interval["label"],
                "start": current_interval["start"],
                "stop": current_interval["stop"],
                "length": current_interval["length"],
                "seq": current_interval["seq"],
                "regions": child,
            }
            nested.append(interval_obj)
            i = next_index

        return nested, i

    result, _ = nest(0, intervals[0]["stop"])
    return result


def fill_gaps(seq, regions, parent_start=0, parent_stop=0):
    if len(regions) == 0:
        return []

    # Insert a filler at the start if necessary
    if regions[0]["start"] > parent_start:
        start = parent_start
        stop = regions[0]["start"]
        s = seq[start:stop]
        regions.insert(
            0,
            {
                "id": "filler_start",
                "label": "filler_start",
                "start": start,
                "stop": stop,
                "length": stop - start,
                "seq": s,
                "regions": [],
            },
        )

    new_regions = []
    for i, region in enumerate(regions):
        # Append the current region
        new_regions.append(region)

        # Recursive call for nested regions
        if "regions" in region:
            region["regions"] = fill_gaps(
                seq, region["regions"], region["start"], region["stop"]
            )

        # Check for gap and insert a filler
        if i < len(regions) - 1 and region["stop"] < regions[i + 1]["start"]:
            filler_id = f'filler_{region["id"]}_{regions[i+1]["id"]}'
            start = region["stop"]
            stop = regions[i + 1]["start"]
            s = seq[start:stop]
            new_regions.append(
                {
                    "id": filler_id,
                    "label": filler_id,
                    "start": start,
                    "stop": stop,
                    "length": stop - start,
                    "seq": s,
                    "regions": [],
                }
            )

    # Insert a filler at the end if necessary
    if new_regions[-1]["stop"] < parent_stop:
        start = new_regions[-1]["stop"]
        stop = parent_stop
        s = seq[start:stop]
        new_regions.append(
            {
                "id": "filler_end",
                "label": "filler_end",
                "start": start,
                "stop": stop,
                "length": stop - start,
                "seq": s,
                "regions": [],
            }
        )

    return new_regions


# convert filled regions to seqspec, must be recursive function
# regions is a list
def convert(regions):
    if len(regions) == 0:
        return []
    new_regions = []
    for r in regions:
        rgn = Region(
            r["id"],
            "",
            r["label"],
            "fixed",
            r["seq"],
            r["length"],
            r["length"],
            None,
            None,
        )
        if len(r["regions"]) > 0:
            rgn.regions = convert(r["regions"])
        new_regions.append(rgn)
    return new_regions

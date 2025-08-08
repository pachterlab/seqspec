"""Check module for seqspec CLI.

This module provides functionality to validate seqspec files against the specification schema.
"""

from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from os import path
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from jsonschema import Draft4Validator

from seqspec.Assay import Assay
from seqspec.utils import file_exists, load_spec


def setup_check_args(parser):
    """Create and configure the check command subparser."""
    subparser = parser.add_parser(
        "check",
        description="""
Validate seqspec file against the specification schema.

Examples:
seqspec check spec.yaml
---
""",
        help="Validate seqspec file against specification",
        formatter_class=RawTextHelpFormatter,
    )
    subparser.add_argument(
        "-o",
        "--output",
        metavar="OUT",
        help="Path to output file",
        type=Path,
        default=None,
    )
    subparser.add_argument(
        "-s",
        "--skip",
        metavar="SKIP",
        help="Skip checks",
        type=str,
        default=None,
        choices=["igvf", "igvf_onlist_skip"],
    )

    subparser.add_argument("yaml", help="Sequencing specification yaml file", type=Path)

    return subparser


def validate_check_args(parser: ArgumentParser, args: Namespace) -> None:
    """Validate the check command arguments."""
    if not Path(args.yaml).exists():
        parser.error(f"Input file does not exist: {args.yaml}")

    if args.output and Path(args.output).exists() and not Path(args.output).is_file():
        parser.error(f"Output path exists but is not a file: {args.output}")


def format_error(errobj, idx=0):
    return f"[error {idx}] {errobj['error_message']}"


def seqspec_check(
    spec: Assay, spec_fn: str, filter_type: Optional[str] = None
) -> List[Dict]:
    """Core functionality to check a seqspec and return filtered errors.

    Args:
        spec: The Assay object to check
        spec_fn: Path to the spec file, used for relative path resolution
        filter_type: Optional filter type to apply to errors (e.g. "igvf", "igvf_onlist_skip")

    Returns:
        List of error dictionaries
    """
    errors = check(spec, spec_fn)

    if filter_type:
        errors = filter_errors(errors, filter_type)
    return errors


def run_check(parser: ArgumentParser, args: Namespace):
    """Run the check command."""
    validate_check_args(parser, args)

    spec = load_spec(args.yaml, strict=False)
    errors = seqspec_check(spec, args.yaml, args.skip)

    if args.output:
        with open(args.output, "w") as f:
            for idx, e in enumerate(errors, 1):
                print(format_error(e, idx), file=f)
    else:
        for idx, e in enumerate(errors, 1):
            print(format_error(e, idx))
    return errors


IGVF_FILTERS = [
    {"error_type": "check_schema", "error_object": "'lib_struct'"},
    {"error_type": "check_schema", "error_object": "'library_protocol'"},
    {"error_type": "check_schema", "error_object": "'library_kit'"},
    {"error_type": "check_schema", "error_object": "'sequence_protocol'"},
    {"error_type": "check_schema", "error_object": "'sequence_kit'"},
    {"error_type": "check_schema", "error_object": "'md5'"},
]
IGVF_ONLIST_SKIP_FILTERS = IGVF_FILTERS + [
    {"error_type": "check_onlist_files_exist", "error_object": "onlist"}
]


def filter_errors(errors, filter_type):
    filters = None
    if filter_type == "igvf":
        filters = IGVF_FILTERS
    elif filter_type == "igvf_onlist_skip":
        filters = IGVF_ONLIST_SKIP_FILTERS

    if filters:
        ferrors = []
        for error in errors:
            # Check if this specific error combination exists in the filters
            should_filter = any(
                error["error_type"] == filter_item["error_type"]
                and error["error_object"] == filter_item["error_object"]
                for filter_item in filters
            )

            # Only keep errors that don't match our filter criteria
            if not should_filter:
                ferrors.append(error)
        return ferrors
    else:
        return errors


def check(spec: Assay, spec_fn: str):
    # Variety of checks against schema
    def check_schema(spec: Assay, spec_fn: str, errors=[], idx=0):
        schema_fn = path.join(path.dirname(__file__), "schema/seqspec.schema.json")
        with open(schema_fn, "r") as stream:
            schema = yaml.load(stream, Loader=yaml.Loader)
        validator = Draft4Validator(schema)
        for idx, error in enumerate(validator.iter_errors(spec.to_dict()), 1):
            err_elements = [repr(index) for index in error.path]
            err_path = f"spec[{']['.join(err_elements)}]"
            errobj = {
                "error_type": "check_schema",
                "error_message": f"{error.message} in {err_path}",
                "error_object": err_elements[-1],
            }
            errors.append(errobj)
        idx += 1
        return (errors, idx)

    # Modalities are unique
    def check_unique_modalities(spec, spec_fn, errors, idx):
        if len(spec.modalities) != len(set(spec.modalities)):
            errobj = {
                "error_type": "check_unique_modalities",
                "error_message": f"modalities [{', '.join(spec.modalities)}] are not unique",
                "error_object": "modalities",
            }
            errors.append(errobj)
            idx += 1
        return (errors, idx)

    # Region_ids of the first level  correspond to the modalities (one per modality)
    def check_region_ids_modalities(spec, spec_fn, errors, idx):
        modes = spec.modalities
        rgns = spec.library_spec
        for r in rgns:
            rid = r.region_id
            if rid not in modes:
                errobj = {
                    "error_type": "check_region_ids_modalities",
                    "error_message": f"region_id '{rid}' of the first level of the spec does not correspond to a modality [{', '.join(modes)}]",
                    "error_object": "region",
                }
                errors.append(errobj)
                idx += 1
        return (errors, idx)

    # Onlist files exist relative to the path of the spec or http
    def check_onlist_files_exist(spec, spec_fn, errors, idx):
        modes = spec.modalities
        olrgns = []
        for m in modes:
            olrgns += [i.onlist for i in spec.get_libspec(m).get_onlist_regions()]

        # check paths relative to spec_fn
        for ol in olrgns:
            if ol.urltype == "local":
                if ol.filename[:-3] == ".gz":
                    check = path.join(path.dirname(spec_fn), ol.filename[:-3])
                    if not path.exists(check):
                        errobj = {
                            "error_type": "check_onlist_files_exist",
                            "error_message": f"{ol.filename[:-3]} does not exist",
                            "error_object": "onlist",
                        }
                        # errors.append(
                        #     f"[error {idx}] {ol.filename[:-3]} does not exist"
                        # )
                        errors.append(errobj)
                        idx += 1
                else:
                    check = path.join(path.dirname(spec_fn), ol.filename)
                    check_gz = path.join(path.dirname(spec_fn), ol.filename + ".gz")
                    if not path.exists(check) and not path.exists(check_gz):
                        errobj = {
                            "error_type": "check_onlist_files_exist",
                            "error_message": f"{ol.filename} does not exist",
                            "error_object": "onlist",
                        }
                        # errors.append(f"[error {idx}] {ol.filename} does not exist")
                        errors.append(errobj)
                        idx += 1
            elif ol.urltype == "http" or ol.urltype == "https" or ol.urltype == "ftp":
                # ping the link with a simple http request to check if the file exists at that URI
                if spec.seqspec_version == "0.3.0":
                    if not file_exists(ol.url):
                        errobj = {
                            "error_type": "check_onlist_files_exist",
                            "error_message": f"{ol.filename} does not exist",
                            "error_object": "onlist",
                        }

                        # errors.append(f"[error {idx}] {ol.filename} does not exist")
                        errors.append(errobj)
                        idx += 1
                else:
                    if not file_exists(ol.filename):
                        errobj = {
                            "error_type": "check_onlist_files_exist",
                            "error_message": f"{ol.filename} does not exist",
                            "error_object": "onlist",
                        }
                        # errors.append(f"[error {idx}] {ol.filename} does not exist")
                        errors.append(errobj)
                        idx += 1
        return (errors, idx)

    # Read ids are unique
    def check_unique_read_ids(spec, spec_fn, errors, idx):
        read_ids = set()
        for read in spec.sequence_spec:
            if read.read_id in read_ids:
                errobj = {
                    "error_type": "check_unique_read_ids",
                    "error_message": f"read_id '{read.read_id}' is not unique across all reads",
                    "error_object": "read",
                }
                errors.append(errobj)
                idx += 1
            else:
                read_ids.add(read.read_id)
        return (errors, idx)

    # Read files exist
    def check_read_files_exist(spec, spec_fn, errors, idx):
        for read in spec.sequence_spec:
            spec_fn = path.dirname(spec_fn)
            for f in read.files:
                if f.urltype == "local":
                    check = path.join(spec_fn, f.filename)
                    if not path.exists(check):
                        errobj = {
                            "error_type": "check_read_files_exist",
                            "error_message": f"{f.filename} does not exist",
                            "error_object": "file",
                        }
                        # errors.append(f"[error {idx}] {f.filename} does not exist")
                        errors.append(errobj)
                        idx += 1
                elif f.urltype == "http" or f.urltype == "https" or f.urltype == "ftp":
                    # ping the link with a simple http request to check if the file exists at that URI
                    if not file_exists(f.url):
                        errobj = {
                            "error_type": "check_read_files_exist",
                            "error_message": f"{f.filename} does not exist",
                            "error_object": "file",
                        }
                        # errors.append(f"[error {idx}] {f.filename} does not exist")
                        errors.append(errobj)
                        idx += 1
        return (errors, idx)

    # Primer ids, strand tuple pairs are unique across all reads
    def check_unique_read_primer_strand_pairs(spec, spec_fn, errors, idx):
        primer_strand_pairs = set()
        for read in spec.sequence_spec:
            if (read.primer_id, read.strand) in primer_strand_pairs:
                errobj = {
                    "error_type": "check_unique_read_primer_strand_pairs",
                    "error_message": f"primer_id '{read.primer_id}' and strand '{read.strand}' tuple is not unique across all reads",
                    "error_object": "read",
                }
                errors.append(errobj)
                idx += 1
            else:
                primer_strand_pairs.add((read.primer_id, read.strand))
        return (errors, idx)

    # TODO add option to check md5sum
    def check_md5sum(spec: Assay, spec_fn, errors, idx):
        return (errors, idx)

    # Region_id is unique across all regions
    def check_unique_region_ids(spec, spec_fn, errors, idx):
        modes = spec.modalities
        rgn_ids = set()
        for m in modes:
            for rgn in spec.get_libspec(m).get_leaves():
                if rgn.region_id in rgn_ids:
                    errobj = {
                        "error_type": "check_unique_region_ids",
                        "error_message": f"region_id '{rgn.region_id}' is not unique across all regions",
                        "error_object": "region",
                    }
                    errors.append(errobj)
                    idx += 1
                else:
                    rgn_ids.add(rgn.region_id)
        return (errors, idx)

    # Modality is in the reads
    def check_read_modalities(spec, spec_fn, errors, idx):
        modes = spec.modalities
        for read in spec.sequence_spec:
            if read.modality not in modes:
                errobj = {
                    "error_type": "check_read_modalities",
                    "error_message": f"read '{read.read_id}' modality '{read.modality}' does not exist in the modalities",
                    "error_object": "read",
                }
                errors.append(errobj)
                idx += 1
        return (errors, idx)

    # check that the unique primer ids exist as a region id in the library_spec
    # TODO is there a better way to get the rgn_ids?
    def check_primer_ids_in_region_ids(spec, spec_fn, errors, idx):
        # first get all unique region_ids
        modes = spec.modalities
        rgn_ids = set()
        for m in modes:
            for rgn in spec.get_libspec(m).get_leaves():
                if rgn.region_id in rgn_ids:
                    pass
                else:
                    rgn_ids.add(rgn.region_id)

        # then check that the primer ids exist in the region_ids
        for read in spec.sequence_spec:
            if read.primer_id not in rgn_ids:
                errobj = {
                    "error_type": "check_primer_ids_in_region_ids",
                    "error_message": f"'{read.read_id}' primer_id '{read.primer_id}' does not exist in the library_spec",
                    "error_object": "read",
                }
                errors.append(errobj)
                idx += 1
        return (errors, idx)

    # NOTE: this is a strong assumption that may be relaxed in the future
    # check that the primer id for each read is in the leaves of the spec for that modality
    # def check_primer_ids_in_libspec_leaves(spec, spec_fn, errors, idx):
    #     for read in spec.sequence_spec:
    #         mode = spec.get_libspec(read.modality)
    #         leaves = mode.get_leaves()
    #         if read.primer_id not in [i.region_id for i in leaves]:
    #             errobj = {
    #                 "error_type": "check_primer_ids_in_libspec_leaves",
    #                 "error_message": f"'{read.read_id}' primer_id '{read.primer_id}' does not exist as an atomic region in the library_spec for modality '{read.modality}'",
    #                 "error_object": "read",
    #             }
    #             errors.append(errobj)
    #             idx += 1
    #     return (errors, idx)

    # check that the max read len is not longer than the max len of the lib spec after the primer
    # for read in spec.sequence_spec:
    #     mode = spec.get_libspec(read.modality)
    #     leaves = mode.get_leaves()
    #     idx = [i.region_id for i in leaves].index(read.primer_id)

    def check_sequence_types(spec, spec_fn, errors, idx):
        modes = spec.modalities

        # if a region has a sequence type "fixed" then it should not contain subregions
        # if a region has a sequence type "joiend" then it should contain subregions
        # if a region has a sequence type "random" then it should not contain subregions and should be all X's
        # if a region has a sequence type "onlist" then it should have an onlist object
        def seqtype_check(rgn, errors, idx):
            # this is a recursive function that iterates through all regions and checks the sequence type
            if rgn.sequence_type == "fixed" and rgn.regions:
                errobj = {
                    "error_type": "check_sequence_types",
                    "error_message": f"'{rgn.region_id}' sequence_type is 'fixed' and contains subregions",
                    "error_object": "region",
                }
                # errors.append(
                #     f"[error {idx}] '{rgn.region_id}' sequence_type is 'fixed' and contains subregions"
                # )
                errors.append(errobj)
                idx += 1
            if rgn.sequence_type == "joined" and not rgn.regions:
                errobj = {
                    "error_type": "check_sequence_types",
                    "error_message": f"'{rgn.region_id}' sequence_type is 'joined' and does not contain subregions",
                    "error_object": "region",
                }
                # errors.append(
                #     f"[error {idx}] '{rgn.region_id}' sequence_type is 'joined' and does not contain subregions"
                # )
                errors.append(errobj)
                idx += 1
            if rgn.sequence_type == "random" and rgn.regions:
                errobj = {
                    "error_type": "check_sequence_types",
                    "error_message": f"'{rgn.region_id}' sequence_type is 'random' and contains subregions",
                    "error_object": "region",
                }
                # errors.append(
                #     f"[error {idx}] '{rgn.region_id}' sequence_type is 'random' and contains subregions"
                # )
                errors.append(errobj)
                idx += 1
            if rgn.sequence_type == "random" and rgn.sequence != "X" * rgn.max_len:
                errobj = {
                    "error_type": "check_sequence_types",
                    "error_message": f"'{rgn.region_id}' sequence_type is 'random' and sequence is not all X's",
                    "error_object": "region",
                }
                errors.append(errobj)
                idx += 1
            if rgn.sequence_type == "onlist" and not rgn.onlist:
                errobj = {
                    "error_type": "check_sequence_types",
                    "error_message": f"'{rgn.region_id}' sequence_type is 'onlist' and does not have an onlist object",
                    "error_object": "region",
                }
                errors.append(errobj)
                idx += 1
            if rgn.regions:
                for r in rgn.regions:
                    errors, idx = seqtype_check(r, errors, idx)
            return (errors, idx)

        for m in modes:
            for rgn in [spec.get_libspec(m)]:
                errors, idx = seqtype_check(rgn, errors, idx)

        return (errors, idx)

    # check the lengths of every region against the max_len, using a recursive function
    def check_region_lengths(spec, spec_fn, errors, idx):
        modes = spec.modalities

        def len_check(rgn, errors, idx):
            if rgn.regions:
                for r in rgn.regions:
                    errors, idx = len_check(r, errors, idx)
            if rgn.max_len < rgn.min_len:
                errobj = {
                    "error_type": "check_region_lengths",
                    "error_message": f"'{rgn.region_id}' max_len is less than min_len",
                    "error_object": "region",
                }
                errors.append(errobj)
                idx += 1
            return (errors, idx)

        for m in modes:
            for rgn in [spec.get_libspec(m)]:
                errors, idx = len_check(rgn, errors, idx)
        return (errors, idx)

    # errors, idx = check_region_lengths(spec, spec_fn, errors, idx)

    # check that the length of the sequence is equal to the max_len using a recursive function
    # an assumption in the code and spec is that the displayed sequence is equal to the max_len
    def check_sequence_lengths(spec, spec_fn, errors, idx):
        modes = spec.modalities

        def seq_len_check(rgn, errors, idx):
            if rgn.regions:
                for r in rgn.regions:
                    errors, idx = seq_len_check(r, errors, idx)
            if rgn.sequence and (
                len(rgn.sequence) < rgn.min_len or len(rgn.sequence) > rgn.max_len
            ):
                # noqa
                errobj = {
                    "error_type": "check_sequence_lengths",
                    "error_message": f"'{rgn.region_id}' sequence '{rgn.sequence}' has length {len(rgn.sequence)}, expected range ({rgn.min_len}, {rgn.max_len})",
                    "error_object": "region",
                }
                errors.append(errobj)
                idx += 1
            return (errors, idx)

        for m in modes:
            for rgn in [spec.get_libspec(m)]:
                errors, idx = seq_len_check(rgn, errors, idx)
        return (errors, idx)

    # check that the number of files in each "File" object for all Read object are all the same length
    def check_read_file_count(spec, spec_fn, errors, idx):
        nfiles = []
        for read in spec.sequence_spec:
            nfiles.append(len(read.files))

        if len(set(nfiles)) != 1:
            errobj = {
                "error_type": "check_read_file_count",
                "error_message": "Reads must have the same number of files",
                "error_object": "read",
            }
            # errors.append(f"[error {idx}] Reads must have the same number of files")
            errors.append(errobj)
            idx += 1
        return (errors, idx)

    # errors, idx = check_read_file_count(spec, spec_fn, errors, idx)

    errors = []
    idx = 0
    checks = {
        "check_schema": check_schema,
        "check_unique_modalities": check_unique_modalities,
        "check_region_ids_modalities": check_region_ids_modalities,
        "check_onlist_files_exist": check_onlist_files_exist,
        "check_unique_read_ids": check_unique_read_ids,
        "check_read_files_exist": check_read_files_exist,
        "check_unique_read_primer_strand_pairs": check_unique_read_primer_strand_pairs,
        "check_unique_region_ids": check_unique_region_ids,
        "check_read_modalities": check_read_modalities,
        "check_primer_ids_in_region_ids": check_primer_ids_in_region_ids,
        # "check_primer_ids_in_libspec_leaves": check_primer_ids_in_libspec_leaves,
        "check_sequence_types": check_sequence_types,
        "check_region_lengths": check_region_lengths,
        "check_sequence_lengths": check_sequence_lengths,
        "check_read_file_count": check_read_file_count,
    }
    for k, v in checks.items():
        # print(k)
        errors, idx = v(spec, spec_fn, errors, idx)

    return errors

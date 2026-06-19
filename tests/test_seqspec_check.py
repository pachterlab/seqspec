import os
import tempfile
from argparse import ArgumentParser
from pathlib import Path
from unittest import TestCase

import pytest
import yaml
from seqspec.Assay import Assay
from seqspec.seqspec_check import seqspec_check
from seqspec.utils import load_spec


def test_seqspec_check(dogmaseq_dig_spec: Assay):
    """Test seqspec_check function"""
    spec = dogmaseq_dig_spec.model_copy(deep=True)

    def localize_onlists(region):
        if region.onlist is not None and region.onlist.urltype in {"http", "https", "ftp"}:
            region.onlist.urltype = "local"
            region.onlist.url = region.onlist.filename + ".gz"
        for child in region.regions:
            localize_onlists(child)

    for region in spec.library_spec:
        localize_onlists(region)

    # Test with valid spec
    diagnostics = seqspec_check(spec=spec)
    assert not any(
        diagnostic["severity"] == "error" for diagnostic in diagnostics
    ), "Valid spec should not emit error diagnostics"

    # Test with invalid spec (missing required fields)
    invalid_spec = Assay(
        seqspec_version="0.3.0",
        assay_id="test",
        name="Test",
        doi="",
        date="20240101",
        description="",
        modalities=[],
        lib_struct="",
        sequence_protocol="",
        sequence_kit="",
        library_protocol="",
        library_kit="",
        sequence_spec=[],
        library_spec=[]
    )
    
    diagnostics = seqspec_check(spec=invalid_spec)
    assert any(
        diagnostic["severity"] == "error" for diagnostic in diagnostics
    ), "Invalid spec should emit error diagnostics"


def test_seqspec_check_warns_on_overlapping_read_regions():
    spec = load_spec(Path("tests/fixtures/check_overlap_warning/spec.yaml"))

    diagnostics = seqspec_check(spec=spec)

    errors = [
        diagnostic for diagnostic in diagnostics if diagnostic["severity"] == "error"
    ]
    warnings = [
        diagnostic
        for diagnostic in diagnostics
        if diagnostic["severity"] == "warning"
    ]

    assert errors == []
    assert len(warnings) == 1
    assert warnings[0]["error_type"] == "check_overlapping_read_regions"
    assert (
        "seqspec index --no-overlap" in warnings[0]["error_message"]
    )
    assert "'barcode'" in warnings[0]["error_message"]
    assert "'umi'" in warnings[0]["error_message"]


def test_seqspec_check_prefers_local_onlist_url():
    spec_path = Path("tests/fixtures/onlist_read_clip/spec.yaml")
    spec = load_spec(spec_path)

    barcode_region = spec.get_libspec("rna").get_region_by_id("barcode_a")[0]
    barcode_region.onlist.filename = "display.txt"

    diagnostics = seqspec_check(spec=spec)

    assert not any(
        diagnostic["error_type"] == "check_onlist_files_exist"
        for diagnostic in diagnostics
    )


def test_seqspec_check_errors_when_local_onlist_url_is_empty():
    spec_path = Path("tests/fixtures/onlist_read_clip/spec.yaml")
    spec = load_spec(spec_path)

    barcode_region = spec.get_libspec("rna").get_region_by_id("barcode_a")[0]
    barcode_region.onlist.url = ""

    diagnostics = seqspec_check(spec=spec)

    assert any(
        diagnostic["error_type"] == "check_onlist_files_exist"
        and diagnostic["error_message"] == "local onlist 'barcode_a.txt' has empty url"
        for diagnostic in diagnostics
    )


def test_seqspec_check_errors_when_local_file_url_is_empty():
    spec_path = Path("tests/fixtures/onlist_read_clip/spec.yaml")
    spec = load_spec(spec_path)

    spec.sequence_spec[0].files[0].url = ""

    diagnostics = seqspec_check(spec=spec)

    assert any(
        diagnostic["error_type"] == "check_read_files_exist"
        and diagnostic["error_message"] == "local file 'rna_read.fastq.gz' has empty url"
        for diagnostic in diagnostics
    )


def test_seqspec_check_validates_region_type_list_shape(dogmaseq_dig_spec: Assay):
    spec = dogmaseq_dig_spec.model_copy(deep=True)
    barcode = spec.get_libspec("rna").get_region_by_id("rna_cell_bc")[0]
    barcode.region_type = ["RGN:partition:cell"]

    diagnostics = seqspec_check(spec=spec)

    assert not any(
        diagnostic["error_type"] == "check_schema"
        and "region_type" in diagnostic["error_object"]
        for diagnostic in diagnostics
    )

    barcode.region_type = []
    diagnostics = seqspec_check(spec=spec)

    assert any(
        diagnostic["error_type"] == "check_schema"
        and "region_type" in diagnostic["error_object"]
        for diagnostic in diagnostics
    )

    barcode.region_type = ["barcode"]
    diagnostics = seqspec_check(spec=spec)

    assert any(
        diagnostic["error_type"] == "check_schema"
        and "region_type" in diagnostic["error_object"]
        for diagnostic in diagnostics
    )


def test_seqspec_check_validates_empty_region_type_list_loaded_from_yaml(tmp_path):
    data = yaml.safe_load(Path("tests/fixtures/spec.yaml").read_text())
    data["library_spec"][2]["regions"][1]["region_type"] = []
    spec_path = tmp_path / "empty_region_type_list.yaml"
    spec_path.write_text(yaml.safe_dump(data, sort_keys=False))

    spec = load_spec(spec_path, strict=False)
    diagnostics = seqspec_check(spec=spec)

    assert spec.library_spec[2].regions[1].region_type == []
    assert any(
        diagnostic["error_type"] == "check_schema"
        and "region_type" in diagnostic["error_object"]
        for diagnostic in diagnostics
    )

import os
import tempfile
from argparse import ArgumentParser
from pathlib import Path
from unittest import TestCase

import pytest
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

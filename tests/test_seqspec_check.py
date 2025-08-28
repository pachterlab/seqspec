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
    # Test with valid spec
    errors = seqspec_check(spec=dogmaseq_dig_spec)
    assert len(errors) == 0  # No errors for valid spec

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
    
    errors = seqspec_check(spec=invalid_spec)
    assert len(errors) > 0  # Should have errors for invalid spec

def test_seqspec_check_igvf_onlist_skip(seqspec_valid_ignore_onlist: Assay):
    errors = seqspec_check(spec=seqspec_valid_ignore_onlist, filter_type="igvf_onlist_skip")
    assert len(errors) == 0

def test_seqspec_check_igvf(seqspec_valid_ignore_onlist: Assay):
    errors = seqspec_check(spec=seqspec_valid_ignore_onlist, filter_type="igvf")
    assert len(errors) == 2
    assert errors[0]["error_type"] == "check_schema"
    assert errors[0]["error_object"] == "'read_id'"
    assert errors[0]["error_message"] == "'1165AJSO' does not match '^IGVF.*' in spec['sequence_spec'][0]['read_id']"
    assert errors[1]["error_type"] == "check_onlist_files_exist"
    assert errors[1]["error_object"] == "onlist"
    assert errors[1]["error_message"] == "IGVFFI7587TJLC.tsv.gz does not exist"
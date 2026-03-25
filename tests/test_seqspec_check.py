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
    errors = seqspec_check(spec=spec)
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

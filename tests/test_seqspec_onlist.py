import pytest
import os
from pathlib import Path
from unittest.mock import patch
from seqspec.seqspec_onlist import (
    get_onlists,
    join_onlist_contents,
    run_onlist,
)
from seqspec.utils import load_spec
from argparse import Namespace, ArgumentParser
from seqspec.seqspec_onlist import Onlist



def test_get_onlists_region(dogmaseq_dig_spec):
    """Test get_onlists with region selector"""
    onlists = get_onlists(dogmaseq_dig_spec, "rna", "region", "rna_cell_bc")
    assert len(onlists) == 1
    assert onlists[0].file_id == "RNA-737K-arc-v1.txt"

def test_get_onlists_region_type(dogmaseq_dig_spec):
    """Test get_onlists with region-type selector"""
    onlists = get_onlists(dogmaseq_dig_spec, "rna", "region-type", "barcode")
    assert len(onlists) > 0
    for onlist in onlists:
        assert onlist is not None

def test_get_onlists_read(dogmaseq_dig_spec):
    """Test get_onlists with read selector"""
    onlists = get_onlists(dogmaseq_dig_spec, "rna", "read", "rna_R1")
    assert len(onlists) == 1

def test_join_onlist_contents_product():
    """Test joining onlists with product format"""
    contents = [["A", "B"], ["1", "2"]]
    joined = join_onlist_contents(contents, "product")
    assert set(joined) == {"A1", "A2", "B1", "B2"}

def test_join_onlist_contents_multi():
    """Test joining onlists with multi format"""
    contents = [["A", "B"], ["1", "2", "3"]]
    joined = join_onlist_contents(contents, "multi")
    assert joined == ["A 1", "B 2", "- 3"]


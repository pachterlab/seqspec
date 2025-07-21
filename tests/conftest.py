"""
Pytest configuration and fixtures for seqspec tests.
"""

import pytest
import tempfile
import os
import yaml
from seqspec.Assay import Assay
from seqspec.Region import Region
from seqspec.Read import Read
from seqspec.utils import load_spec


@pytest.fixture
def sample_assay():
    """Create a sample assay for testing."""
    return Assay(
        seqspec_version="0.3.0",
        assay_id="test_assay",
        name="Test Assay",
        doi="https://doi.org/10.1101/test",
        date="20240101",
        description="Test description",
        modalities=["RNA"],
        lib_struct="test_structure",
        sequence_protocol="test_protocol",
        sequence_kit="test_kit",
        library_protocol="test_lib_protocol",
        library_kit="test_lib_kit",
        sequence_spec=[],
        library_spec=[]
    )


@pytest.fixture
def sample_region():
    """Create a sample region for testing."""
    return Region(
        region_id="test_region",
        region_type="barcode",
        name="Test Barcode",
        sequence_type="fixed",
        sequence="ATCG",
        min_len=4,
        max_len=4
    )


@pytest.fixture
def sample_read():
    """Create a sample read for testing."""
    return Read(
        read_id="test_read",
        name="Test Read",
        modality="RNA",
        primer_id="test_primer",
        min_len=100,
        max_len=150,
        strand="pos"
    )


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        yield f.name
        os.unlink(f.name)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir 


@pytest.fixture(scope="session")
def dogmaseq_dig_spec():
    """
    Load the dogmaseq-dig spec from file
    """
    spec_path = "tests/fixtures/spec.yaml"
    return load_spec(spec_path)


@pytest.fixture(scope="function")
def temp_spec_file(tmp_path):
    """
    Create a temporary spec file (copy of dogmaseq-dig)
    """
    spec_path = "tests/fixtures/spec.yaml"
    temp_spec_path = tmp_path / "spec.yaml"
    with open(spec_path, "r") as f_in, open(temp_spec_path, "w") as f_out:
        f_out.write(f_in.read())
    return str(temp_spec_path)


@pytest.fixture(scope="function")
def temp_spec(dogmaseq_dig_spec: Assay):
    """
    Create a deepcopy of the dogmaseq-dig spec for modification
    """
    return dogmaseq_dig_spec.model_copy(deep=True) 
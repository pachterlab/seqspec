import os
import tempfile
import gzip
from unittest.mock import patch, mock_open, MagicMock
from io import StringIO
import io

import pytest

from seqspec.utils import (
    load_spec_stream,
    read_local_list,
    read_remote_list,
    get_remote_auth_token,
    map_read_id_to_regions,
    write_read,
    yield_onlist_contents,
)
from seqspec.Assay import Assay
from seqspec.Region import Region, Onlist
from seqspec.Read import Read


def test_load_spec_stream_valid():
    """Test loading a valid spec from a stream"""
    spec_content = """
seqspec_version: 0.2.0
assay_id: MyAssay
name: Test Assay
doi: "10.1234/test.doi"
date: "2023-01-01"
description: "A test assay"
modalities: ["RNA"]
lib_struct: "Test structure"
sequence_spec: []
library_spec: []
"""
    with StringIO(spec_content) as stream:
        spec = load_spec_stream(stream)

    assert isinstance(spec, Assay)
    assert spec.assay_id == "MyAssay"

def test_write_read():
    # Create a dummy Read object
    read = Read(
        read_id="read1",
        name="Read 1",
        modality="RNA",
        primer_id="primer1",
        min_len=4,
        max_len=4,
        strand="+",
    )

    # Use a temporary file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        file_path = tmp.name
        write_read(read.name, "ATCG", "IIII", tmp)

        # Read back the content to verify
        tmp.seek(0)
        content = tmp.read()
        assert "Read 1" in content
        assert "ATCG" in content
        assert "IIII" in content

    # Clean up the temporary file
    os.remove(file_path)



def test_map_read_id_to_regions():
    """Test mapping read ID to regions."""
    # Create a mock spec
    spec = Assay(
        assay_id="test_assay",
        name="Test Assay",
        doi="test_doi",
        date="2023-01-01",
        description="Test description",
        modalities=["RNA"],
        lib_struct="test_lib_struct",
        sequence_protocol="test_seq_protocol",
        sequence_kit="test_seq_kit",
        library_protocol="test_lib_protocol",
        library_kit="test_lib_kit",
        sequence_spec=[
            Read(
                read_id="read1",
                name="Read 1",
                modality="RNA",
                primer_id="primer1",
                min_len=20,
                max_len=20,
                strand="+",
            )
        ],
        library_spec=[
            Region(
                region_id="RNA",
                region_type="RNA",
                name="RNA region",
                sequence_type="joined",
                sequence="ACGTACGTACGTACGTACGT",
                regions=[
                    Region(
                        region_id="primer1",
                        region_type="primer",
                        name="Primer",
                        sequence_type="fixed",
                        sequence="ACGTACGTACGTACGTACGT",
                        min_len=20,
                        max_len=20,

                    ),
                    Region(
                        region_id="barcode",
                        region_type="barcode",
                        name="barcode",
                        sequence_type="random",
                        sequence="ACGTACGTACGTACGTACGT",
                        min_len=20,
                        max_len=20,

                    )
                ],
            )
        ],
    )

    read, regions = map_read_id_to_regions(spec, "RNA", "read1")

    assert read.read_id == "read1"
    assert len(regions) == 1
    assert regions[0].region_id == "barcode"

def test_map_read_id_to_regions_invalid_modality():
    """Test mapping read ID with an invalid modality."""
    spec = Assay(
        assay_id="test_assay",
        name="Test Assay",
        doi="test_doi",
        date="2023-01-01",
        description="Test description",
        modalities=["RNA"],
        lib_struct="test_lib_struct",
        sequence_protocol="test_seq_protocol",
        sequence_kit="test_seq_kit",
        library_protocol="test_lib_protocol",
        library_kit="test_lib_kit",
        sequence_spec=[],
        library_spec=[],
    )
    with pytest.raises(ValueError):
        map_read_id_to_regions(spec, "DNA", "read1")

def test_map_read_id_to_regions_invalid_read_id():
    """Test mapping read ID with an invalid read ID."""
    spec = Assay(
        assay_id="test_assay",
        name="Test Assay",
        doi="test_doi",
        date="2023-01-01",
        description="Test description",
        modalities=["RNA"],
        lib_struct="test_lib_struct",
        sequence_protocol="test_seq_protocol",
        sequence_kit="test_seq_kit",
        library_protocol="test_lib_protocol",
        library_kit="test_lib_kit",
        sequence_spec=[
            Read(
                read_id="read1",
                name="Read 1",
                modality="RNA",
                primer_id="primer1",
                min_len=10,
                max_len=20,
                strand="+",
            )
        ],
        library_spec=[],
    )
    with pytest.raises(IndexError):
        map_read_id_to_regions(spec, "RNA", "read2") 
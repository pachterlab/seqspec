import os
import tempfile
import gzip
from unittest.mock import patch, mock_open, MagicMock
from io import StringIO
from pathlib import Path

import pytest

from seqspec.utils import (
    is_remote_source,
    load_spec_stream,
    load_spec,
    local_resource_url,
    read_local_list,
    read_remote_list,
    get_remote_auth_token,
    local_onlist_locator,
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


def test_is_remote_source():
    assert is_remote_source("https://example.org/spec.yaml")
    assert is_remote_source("ftp://example.org/spec.yaml")
    assert not is_remote_source("tests/fixtures/spec.yaml")


def test_load_spec_reads_remote_yaml():
    payload = Path("tests/fixtures/spec.yaml").read_bytes()
    response = MagicMock()
    response.content = payload
    response.raise_for_status.return_value = None

    with patch("seqspec.utils.get_remote_auth_token", return_value=None), patch(
        "seqspec.utils.requests.get", return_value=response
    ) as mock_get:
        spec = load_spec("https://example.org/spec.yaml")

    assert spec.assay_id == "DOGMAseq-DIG"
    assert spec._spec_path is None
    assert spec._spec_source == "https://example.org/spec.yaml"
    mock_get.assert_called_once_with("https://example.org/spec.yaml", auth=None)


def test_load_spec_reads_remote_gzipped_yaml():
    payload = gzip.compress(Path("tests/fixtures/spec.yaml").read_bytes())
    response = MagicMock()
    response.content = payload
    response.raise_for_status.return_value = None

    with patch("seqspec.utils.get_remote_auth_token", return_value=None), patch(
        "seqspec.utils.requests.get", return_value=response
    ) as mock_get:
        spec = load_spec("https://example.org/spec.yaml.gz")

    assert spec.assay_id == "DOGMAseq-DIG"
    assert spec._spec_path is None
    assert spec._spec_source == "https://example.org/spec.yaml.gz"
    mock_get.assert_called_once_with("https://example.org/spec.yaml.gz", auth=None)

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


def test_map_read_id_to_multi_level_regions():
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
                primer_id="meta_primer",
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
                        region_id="meta_primer",
                        region_type="meta_primer",
                        name="Primer",
                        sequence_type="fixed",
                        sequence="ACGTACGTACGTACGTACGT",
                        min_len=20,
                        max_len=20,
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
                                        region_id="fixed_seq",
                                        region_type="named",
                                        name="fixed",
                                        sequence_type="fixed",
                                        sequence="ACGTACGTACGTACGTACGT",
                                        min_len=20,
                                        max_len=20,
                            ),
                        ]
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
    with pytest.raises(IndexError):
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


def test_local_onlist_locator_prefers_url_when_present():
    onlist = Onlist(
        file_id="ol1",
        filename="display.txt",
        filetype="txt",
        filesize=0,
        url="nested/whitelist.txt",
        urltype="local",
        md5="",
    )

    assert local_onlist_locator(onlist) == "nested/whitelist.txt"


def test_local_onlist_locator_errors_when_url_is_empty():
    onlist = Onlist(
        file_id="ol1",
        filename="display.txt",
        filetype="txt",
        filesize=0,
        url="",
        urltype="local",
        md5="",
    )

    with pytest.raises(ValueError, match="local onlist 'display.txt' has empty url"):
        local_onlist_locator(onlist)


def test_read_local_list_prefers_url_when_present(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "whitelist.txt").write_text("AAAA\nCCCC\n")

    onlist = Onlist(
        file_id="ol1",
        filename="display.txt",
        filetype="txt",
        filesize=0,
        url="nested/whitelist.txt",
        urltype="local",
        md5="",
    )

    assert read_local_list(onlist, str(tmp_path)) == ["AAAA", "CCCC"]


def test_read_local_list_projects_column_after_skipping_header():
    onlist = Onlist(
        file_id="tabular_onlist",
        filename="tabular_onlist.txt",
        filetype="txt",
        filesize=0,
        url="tests/fixtures/tabular_onlist.txt",
        urltype="local",
        md5="",
        sequence_column_index=1,
        skip_rows=1,
    )

    assert read_local_list(onlist) == [
        "TCAGTTGTCGAAGG",
        "CTGGACCTAATACC",
    ]


def test_read_local_list_projects_gzipped_column_after_skipping_header(tmp_path):
    path = tmp_path / "plate.tsv.gz"
    path.write_bytes(gzip.compress(b"Name Barcode\nA01 AAAA\nA02 CCCC\n"))
    onlist = Onlist(
        file_id="local_plate",
        filename="plate.tsv.gz",
        filetype="tsv",
        filesize=0,
        url="plate.tsv.gz",
        urltype="local",
        md5="",
        sequence_column_index=1,
        skip_rows=1,
    )

    assert read_local_list(onlist, str(tmp_path)) == ["AAAA", "CCCC"]


def test_read_local_list_errors_when_projection_column_is_missing(tmp_path):
    (tmp_path / "malformed.txt").write_text("Name Barcode\nA01\n")
    onlist = Onlist(
        file_id="malformed",
        filename="malformed.txt",
        filetype="txt",
        filesize=0,
        url="malformed.txt",
        urltype="local",
        md5="",
        sequence_column_index=1,
        skip_rows=1,
    )

    with pytest.raises(ValueError, match="row 2 has 1 field.*column index 1"):
        read_local_list(onlist, str(tmp_path))


def test_read_remote_list_projects_column_after_skipping_header():
    onlist = Onlist(
        file_id="remote_plate",
        filename="plate.tsv",
        filetype="tsv",
        filesize=0,
        url="https://example.org/plate.tsv",
        urltype="https",
        md5="",
        sequence_column_index=1,
        skip_rows=1,
    )
    response = MagicMock()
    response.content = b"Name Barcode\nA01 AAAA\nA02 CCCC\n"

    with (
        patch("seqspec.utils.get_remote_auth_token", return_value=None),
        patch("seqspec.utils.requests.get", return_value=response),
    ):
        assert read_remote_list(onlist) == ["AAAA", "CCCC"]


def test_read_remote_list_projects_gzipped_column_after_skipping_header():
    onlist = Onlist(
        file_id="remote_plate",
        filename="plate.tsv.gz",
        filetype="tsv",
        filesize=0,
        url="https://example.org/plate.tsv.gz",
        urltype="https",
        md5="",
        sequence_column_index=1,
        skip_rows=1,
    )
    response = MagicMock()
    response.content = gzip.compress(b"Name Barcode\nA01 AAAA\nA02 CCCC\n")

    with (
        patch("seqspec.utils.get_remote_auth_token", return_value=None),
        patch("seqspec.utils.requests.get", return_value=response),
    ):
        assert read_remote_list(onlist) == ["AAAA", "CCCC"]


def test_local_resource_url_errors_when_url_is_empty():
    with pytest.raises(ValueError, match="local file 'display.fastq.gz' has empty url"):
        local_resource_url("", "display.fastq.gz", "file")

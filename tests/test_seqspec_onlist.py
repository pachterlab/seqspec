from pathlib import Path
from unittest.mock import patch

import pytest

from seqspec.seqspec_onlist import (
    Onlist,
    download_onlists_to_path,
    get_onlists,
    get_onlist_urls,
    join_onlist_contents,
    join_onlists_and_save,
)
from seqspec.utils import load_spec


def test_get_onlists_region(dogmaseq_dig_spec):
    """Test get_onlists with region selector"""
    onlists = get_onlists(dogmaseq_dig_spec, "rna", "region", "rna_cell_bc")
    assert len(onlists) == 1
    assert onlists[0].file_id == "RNA-737K-arc-v1.txt"


def test_get_onlists_region_type_raises_for_ambiguous_reads(dogmaseq_dig_spec):
    """Test get_onlists with region-type selector when matches span reads."""
    with pytest.raises(ValueError, match="matches regions in multiple reads"):
        get_onlists(dogmaseq_dig_spec, "rna", "region-type", "barcode")


def test_get_onlists_read(dogmaseq_dig_spec):
    """Test get_onlists with read selector"""
    onlists = get_onlists(dogmaseq_dig_spec, "rna", "read", "rna_R1")
    assert len(onlists) == 1


def test_get_onlists_read_respects_read_window():
    spec = load_spec("tests/fixtures/onlist_read_clip/spec.yaml")
    onlists = get_onlists(spec, "rna", "read", "rna_read")

    assert [onlist.file_id for onlist in onlists] == ["barcode_a.txt"]


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


def remote_onlist() -> Onlist:
    return Onlist(
        file_id="remote_list",
        filename="remote.txt.gz",
        filetype="txt.gz",
        filesize=123,
        url="https://example.org/remote.txt.gz",
        urltype="https",
        md5="abc",
    )


def test_download_onlists_to_path_threads_auth_profile(tmp_path):
    calls = []

    def fake_read_remote_list(onlist, base_path="", auth_profile=None):
        calls.append(
            {
                "file_id": onlist.file_id,
                "base_path": base_path,
                "auth_profile": auth_profile,
            }
        )
        return ["AAA", "CCC"]

    output_path = tmp_path / "joined.txt"
    with patch("seqspec.seqspec_onlist.read_remote_list", side_effect=fake_read_remote_list):
        downloaded = download_onlists_to_path(
            [remote_onlist()],
            output_path,
            tmp_path,
            auth_profile="igvf",
        )

    assert calls == [
        {
            "file_id": "remote_list",
            "base_path": "",
            "auth_profile": "igvf",
        }
    ]
    assert len(downloaded) == 1
    assert downloaded[0]["file_id"] == "remote_list"
    assert downloaded[0]["url"].endswith("remote_list_joined.txt")
    assert Path(downloaded[0]["url"]).read_text().splitlines() == ["AAA", "CCC"]


def test_download_projected_local_onlist_writes_normalized_copy(tmp_path):
    source = tmp_path / "plate.tsv"
    source.write_text("Name Barcode\nA01 AAAA\nA02 CCCC\n")
    onlist = Onlist(
        file_id="plate",
        filename="plate.tsv",
        filetype="tsv",
        filesize=source.stat().st_size,
        url="plate.tsv",
        urltype="local",
        md5="",
        sequence_column_index=1,
        skip_rows=1,
    )

    downloaded = download_onlists_to_path(
        [onlist], tmp_path / "normalized.txt", tmp_path
    )

    normalized = Path(downloaded[0]["url"])
    assert normalized != source
    assert normalized.read_text().splitlines() == ["AAAA", "CCCC"]


def test_join_onlists_and_save_threads_auth_profile(tmp_path):
    calls = []

    def fake_read_remote_list(onlist, base_path="", auth_profile=None):
        calls.append(
            {
                "file_id": onlist.file_id,
                "base_path": base_path,
                "auth_profile": auth_profile,
            }
        )
        return ["AAA", "CCC"]

    output_path = tmp_path / "product.txt"
    with patch("seqspec.seqspec_onlist.read_remote_list", side_effect=fake_read_remote_list):
        result_path = join_onlists_and_save(
            [remote_onlist()],
            "product",
            output_path,
            tmp_path,
            auth_profile="igvf",
        )

    assert calls == [
        {
            "file_id": "remote_list",
            "base_path": "",
            "auth_profile": "igvf",
        }
    ]
    assert result_path == str(output_path)
    assert output_path.read_text().splitlines() == ["AAA", "CCC"]


def test_product_onlist_matches_between_read_and_region_type_for_issue_68(tmp_path):
    fixture_dir = Path("tests/fixtures/onlist_issue_68")
    spec = load_spec(fixture_dir / "spec.yaml")

    read_output = tmp_path / "read_product.txt"
    region_type_output = tmp_path / "region_type_product.txt"

    join_onlists_and_save(
        get_onlists(spec, "rna", "read", "rna_read"),
        "product",
        read_output,
        fixture_dir,
    )
    join_onlists_and_save(
        get_onlists(spec, "rna", "region-type", "barcode"),
        "product",
        region_type_output,
        fixture_dir,
    )

    read_lines = read_output.read_text().splitlines()
    region_type_lines = region_type_output.read_text().splitlines()

    assert read_lines == ["TTAA", "TTAC", "TGAA", "TGAC"]
    assert region_type_lines == read_lines


def test_get_onlists_region_type_uses_read_order_when_unique():
    spec = load_spec("tests/fixtures/onlist_issue_68/spec.yaml")
    onlists = get_onlists(spec, "rna", "region-type", "barcode")
    assert [onlist.file_id for onlist in onlists] == ["barcode_b.txt", "barcode_a.txt"]


def test_region_type_onlist_errors_when_matches_span_multiple_reads():
    spec = load_spec("tests/fixtures/onlist_ambiguous_region_type/spec.yaml")

    with pytest.raises(ValueError, match="matches regions in multiple reads"):
        get_onlists(spec, "rna", "region-type", "barcode")


def test_get_onlist_urls_prefers_local_url(tmp_path):
    onlist = Onlist(
        file_id="local_list",
        filename="display.txt",
        filetype="txt",
        filesize=0,
        url="nested/whitelist.txt",
        urltype="local",
        md5="",
    )

    urls = get_onlist_urls([onlist], tmp_path)
    assert urls == [
        {
            "file_id": "local_list",
            "url": str(tmp_path / "nested" / "whitelist.txt"),
        }
    ]


def test_join_onlists_and_save_reads_local_onlists_from_url(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "whitelist.txt").write_text("AAAA\nCCCC\n")

    onlist = Onlist(
        file_id="local_list",
        filename="display.txt",
        filetype="txt",
        filesize=0,
        url="nested/whitelist.txt",
        urltype="local",
        md5="",
    )
    output = tmp_path / "joined.txt"

    result_path = join_onlists_and_save([onlist], "product", output, tmp_path)

    assert result_path == str(output)
    assert output.read_text().splitlines() == ["AAAA", "CCCC"]

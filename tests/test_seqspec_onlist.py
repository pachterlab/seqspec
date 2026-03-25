import os
from argparse import ArgumentParser, Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

from seqspec.seqspec_onlist import (
    Onlist,
    download_onlists_to_path,
    get_onlists,
    join_onlist_contents,
    join_onlists_and_save,
    run_onlist,
)


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

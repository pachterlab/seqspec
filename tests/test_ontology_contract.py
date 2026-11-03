"""Exercise role semantics through the Python and native CLIs on one real fixture."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from seqspec.region_type import (
    REGISTERED_REGION_TYPE_TERMS,
    is_cell_barcode,
    is_cell_or_nucleus_barcode,
    region_type_matches,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(params=["python", "rust"])
def cli(request, tmp_path):
    if request.param == "python":
        command = [sys.executable, "-m", "seqspec.main"]
    else:
        native = Path(os.environ.get("SEQSPEC_RUST_BIN", ROOT / "target/debug/seqspec"))
        if not native.exists():
            pytest.skip("Build the Rust CLI or set SEQSPEC_RUST_BIN")
        command = [str(native)]

    def run(*args):
        return subprocess.run(
            command + list(args),
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            env=dict(
                os.environ,
                PYTHONPATH=str(ROOT),
                MPLBACKEND="Agg",
                MPLCONFIGDIR=str(tmp_path),
            ),
        )

    return run


def spec_file(tmp_path, types):
    source = ROOT / "tests/fixtures/onlist_issue_68"
    document = yaml.safe_load((source / "spec.yaml").read_text())
    document["seqspec_version"] = "0.5.0"
    for region, terms in zip(document["library_spec"][0]["regions"], types):
        region["region_type"] = terms
    for name in ("barcode_a.txt", "barcode_b.txt"):
        (tmp_path / name).write_bytes((source / name).read_bytes())
    path = tmp_path / "spec.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False))
    return str(path)


def test_bundled_registry_and_exact_identity():
    registry = yaml.safe_load((ROOT / "docs/region_ontology_registry.yaml").read_text())
    bundled = json.loads((ROOT / "seqspec/schema/region_terms.json").read_text())
    assert bundled["version"] == registry["ontology_version"]
    assert set(REGISTERED_REGION_TYPE_TERMS) == set(registry["terms"])
    assert not is_cell_barcode(["RGN:partition:nucleus"])
    assert is_cell_or_nucleus_barcode(["RGN:partition:nucleus"])
    assert not region_type_matches("index7", "index5")
    assert not region_type_matches(["RGN:classify:perturbation"], "sgrna_target")


@pytest.mark.parametrize(
    "terms,expected",
    [
        (["RGN:partition:nucleus"], "4C"),
        (["RGN:technical:index7"], "4B"),
        (["RGN:partition:library", "RGN:technical:index7"], "4B"),
    ],
)
def test_fgbio_roles(cli, tmp_path, terms, expected):
    spec = spec_file(tmp_path, [terms, terms])
    result = cli("index", "-m", "rna", "-i", "rna_read", "-t", "fgbio", spec)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected


def test_index_queries_select_the_right_list_and_interval(cli, tmp_path):
    spec = spec_file(
        tmp_path,
        [["RGN:technical:index5"], ["RGN:partition:library", "RGN:technical:index7"]],
    )
    for query, region_id, filename, coordinate in [
        ("index5", "barcode_a", "barcode_a.txt", "3:4"),
        ("index7", "barcode_b", "barcode_b.txt", "1:2"),
    ]:
        found = cli("find", "-m", "rna", "-s", "region-type", "-i", query, spec)
        assert found.returncode == 0, found.stderr
        assert [r["region_id"] for r in yaml.safe_load(found.stdout)] == [region_id]
        onlist = cli("onlist", "-m", "rna", "-s", "region-type", "-i", query, spec)
        assert onlist.returncode == 0, onlist.stderr
        assert [Path(line).name for line in onlist.stdout.splitlines()] == [filename]
        index = cli(
            "index",
            "-m",
            "rna",
            "-i",
            "rna_read",
            "-t",
            "seqkit",
            "--subregion-type",
            query,
            spec,
        )
        assert index.returncode == 0, index.stderr
        assert index.stdout.strip() == coordinate


@pytest.mark.parametrize(
    "terms,status,diagnostic",
    [
        (["RGN:"], 1, "Malformed ontology term"),
        (["RGN:partition:cell:extra"], 1, "Malformed ontology term"),
        (["RGN:partition:cel"], 0, "[warning"),
        (["RGN:new_role:new_target"], 0, "[warning"),
        (["RGN:unknown:unclassified"], 0, "Unclassified role"),
        (["RGN:unknown:unclassified", "RGN:partition:cell"], 1, "must stand alone"),
        (["RGN:partition:nucleus"], 0, ""),
        ([], 1, "region_type"),
    ],
)
def test_check_ontology_diagnostics(cli, tmp_path, terms, status, diagnostic):
    spec = spec_file(tmp_path, [terms])
    result = cli("check", "--skip", "external", spec)
    assert result.returncode == status, result.stdout + result.stderr
    assert diagnostic in result.stdout
    if not diagnostic:
        assert result.stdout == ""


def test_no_container_inheritance(cli, tmp_path):
    spec = spec_file(tmp_path, [["RGN:partition:nucleus"], ["RGN:partition:cell"]])
    document = yaml.safe_load(Path(spec).read_text())
    document["library_spec"][0]["region_type"] = ["RGN:measure:genome"]
    Path(spec).write_text(yaml.safe_dump(document, sort_keys=False))
    container = cli(
        "find", "-m", "rna", "-s", "region-type", "-i", "RGN:measure:genome", spec
    )
    assert container.returncode == 0, container.stderr
    assert [r["region_id"] for r in yaml.safe_load(container.stdout)] == ["rna"]
    result = cli(
        "find", "-m", "rna", "-s", "region-type", "-i", "RGN:partition:nucleus", spec
    )
    assert result.returncode == 0, result.stderr
    assert [r["region_id"] for r in yaml.safe_load(result.stdout)] == ["barcode_a"]

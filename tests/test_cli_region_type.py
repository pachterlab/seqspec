import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_python_cli(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    env["MPLCONFIGDIR"] = str(tmp_path / "mplconfig")
    env["PYTHONPATH"] = f"{REPO_ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}"
    (tmp_path / "mplconfig").mkdir(exist_ok=True)
    return subprocess.run(
        [sys.executable, "-m", "seqspec.main", *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=90,
        check=True,
    )


def run_python_cli_raw(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    env["MPLCONFIGDIR"] = str(tmp_path / "mplconfig")
    env["PYTHONPATH"] = f"{REPO_ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}"
    (tmp_path / "mplconfig").mkdir(exist_ok=True)
    return subprocess.run(
        [sys.executable, "-m", "seqspec.main", *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )


def copy_onlist_fixture(tmp_path: Path) -> Path:
    fixture_dir = REPO_ROOT / "tests" / "fixtures" / "onlist_issue_68"
    for name in ["spec.yaml", "barcode_a.txt", "barcode_b.txt"]:
        shutil.copy(fixture_dir / name, tmp_path / name)
    (tmp_path / "rna_read.fastq.gz").write_text("")
    return tmp_path / "spec.yaml"


def test_python_cli_check_exit_status_tracks_error_diagnostics(tmp_path):
    source = copy_onlist_fixture(tmp_path)

    valid = run_python_cli_raw(tmp_path, "check", "-s", "igvf_onlist_skip", str(source))
    assert valid.returncode == 0, valid.stdout + valid.stderr

    invalid = tmp_path / "invalid-region-type.yaml"
    data = yaml.safe_load(source.read_text())
    data["library_spec"][0]["regions"][0]["region_type"] = []
    invalid.write_text(yaml.safe_dump(data, sort_keys=False))

    result = run_python_cli_raw(tmp_path, "check", "-s", "igvf_onlist_skip", str(invalid))
    assert result.returncode == 1
    assert "region_type" in result.stdout


def test_python_cli_region_type_ontology_roundtrip_and_queries(tmp_path):
    source = copy_onlist_fixture(tmp_path)
    upgraded = tmp_path / "upgraded.yaml"

    run_python_cli(tmp_path, "upgrade", "-o", str(upgraded), str(source))
    upgraded_data = yaml.safe_load(upgraded.read_text())
    assert upgraded_data["seqspec_version"] == "0.5.0"
    assert upgraded_data["library_spec"][0]["regions"][0]["region_type"] == [
        "RGN:partition:cell"
    ]

    found = run_python_cli(
        tmp_path,
        "find",
        "-m",
        "rna",
        "-s",
        "region-type",
        "-i",
        "RGN:partition:cell",
        str(upgraded),
    ).stdout
    assert "!!python" not in found
    found_regions = yaml.safe_load(found)
    assert [region["region_id"] for region in found_regions] == [
        "barcode_a",
        "barcode_b",
    ]

    onlist = run_python_cli(
        tmp_path,
        "onlist",
        "-m",
        "rna",
        "-s",
        "region-type",
        "-i",
        "RGN:partition:cell",
        str(upgraded),
    ).stdout.splitlines()
    assert [Path(line).name for line in onlist] == ["barcode_b.txt", "barcode_a.txt"]

    joined = tmp_path / "joined.txt"
    run_python_cli(
        tmp_path,
        "onlist",
        "-m",
        "rna",
        "-s",
        "region-type",
        "-i",
        "RGN:partition:cell",
        "-f",
        "product",
        "-o",
        str(joined),
        str(upgraded),
    )
    assert joined.read_text().splitlines() == ["TTAA", "TTAC", "TGAA", "TGAC"]


def test_python_cli_region_type_ontology_index_and_file_outputs(tmp_path):
    upgraded = tmp_path / "dogma-upgraded.yaml"
    run_python_cli(
        tmp_path,
        "upgrade",
        "-o",
        str(upgraded),
        str(REPO_ROOT / "tests" / "fixtures" / "spec.yaml"),
    )

    files = run_python_cli(
        tmp_path,
        "file",
        "-m",
        "rna",
        "-s",
        "region-type",
        "-i",
        "RGN:partition:cell",
        "-f",
        "list",
        "-k",
        "file_id",
        str(upgraded),
    ).stdout.strip()
    assert files == "rna_cell_bc\tRNA-737K-arc-v1.txt\tRNA-737K-arc-v1.txt"

    fgbio = run_python_cli(
        tmp_path,
        "index",
        "-m",
        "rna",
        "-s",
        "read",
        "-i",
        "rna_R1,rna_R2",
        "-t",
        "fgbio",
        str(upgraded),
    ).stdout.strip()
    assert fgbio == "16C12M 102T"

    seqkit = run_python_cli(
        tmp_path,
        "index",
        "-m",
        "rna",
        "-s",
        "read",
        "-i",
        "rna_R1",
        "--subregion-type",
        "RGN:partition:cell",
        "-t",
        "seqkit",
        str(upgraded),
    ).stdout.strip()
    assert seqkit == "1:16"


def test_python_cli_upgrade_legacy_versions_to_region_type_ontology(tmp_path):
    upgraded_02 = tmp_path / "legacy-02-upgraded.yaml"
    run_python_cli(
        tmp_path,
        "upgrade",
        "-o",
        str(upgraded_02),
        str(REPO_ROOT / "tests" / "fixtures" / "legacy_0_2_missing_fields.yaml"),
    )
    legacy_02 = yaml.safe_load(upgraded_02.read_text())
    assert legacy_02["seqspec_version"] == "0.5.0"
    assert legacy_02["sequence_spec"][0]["files"][0]["file_id"] == "rna_R1"
    assert legacy_02["library_spec"][0]["regions"][1]["region_type"] == [
        "RGN:partition:cell"
    ]

    found_barcode = run_python_cli(
        tmp_path,
        "find",
        "-m",
        "rna",
        "-s",
        "region-type",
        "-i",
        "RGN:partition:cell",
        str(upgraded_02),
    ).stdout
    assert [region["region_id"] for region in yaml.safe_load(found_barcode)] == ["barcode"]

    upgraded_03 = tmp_path / "legacy-03-upgraded.yaml"
    run_python_cli(
        tmp_path,
        "upgrade",
        "-o",
        str(upgraded_03),
        str(REPO_ROOT / "tests" / "fixtures" / "legacy_0_3_scalar_protocols.yaml"),
    )
    legacy_03 = yaml.safe_load(upgraded_03.read_text())
    assert legacy_03["seqspec_version"] == "0.5.0"
    assert legacy_03["sequence_protocol"][0]["protocol_id"] == "NovaSeq"
    assert legacy_03["library_spec"][0]["regions"][1]["region_type"] == [
        "RGN:partition:molecule"
    ]

    found_umi = run_python_cli(
        tmp_path,
        "find",
        "-m",
        "rna",
        "-s",
        "region-type",
        "-i",
        "RGN:partition:molecule",
        str(upgraded_03),
    ).stdout
    assert [region["region_id"] for region in yaml.safe_load(found_umi)] == ["umi"]

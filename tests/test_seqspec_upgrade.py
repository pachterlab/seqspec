from pathlib import Path

import yaml

from seqspec.seqspec_upgrade import seqspec_upgrade
from seqspec.seqspec_check import seqspec_check
from seqspec.seqspec_file import seqspec_file
from seqspec.seqspec_find import seqspec_find
from seqspec.seqspec_index import format_index, seqspec_index
from seqspec.seqspec_onlist import get_onlists
from seqspec.region_type import region_type_terms
from seqspec.utils import load_spec


def test_seqspec_upgrade_promotes_0_3_to_0_5():
    spec = load_spec(Path("tests/fixtures/legacy_0_3_scalar_protocols.yaml"), strict=False)
    assert spec.seqspec_version == "0.3.0"

    upgraded = seqspec_upgrade(spec, spec.seqspec_version)

    assert upgraded.seqspec_version == "0.5.0"


def test_seqspec_upgrade_promotes_0_2_to_0_5_and_adds_files():
    spec = load_spec(Path("tests/fixtures/legacy_0_2_missing_fields.yaml"), strict=False)
    assert spec.seqspec_version == "0.2.0"
    assert spec.sequence_spec[0].files == []

    upgraded = seqspec_upgrade(spec, spec.seqspec_version)

    assert upgraded.seqspec_version == "0.5.0"
    assert len(upgraded.sequence_spec[0].files) == 1
    assert upgraded.sequence_spec[0].files[0].file_id == upgraded.sequence_spec[0].read_id


def test_seqspec_upgrade_converts_region_types_to_ontology_terms():
    spec = load_spec(Path("tests/fixtures/spec.yaml"), strict=False)

    upgraded = seqspec_upgrade(spec, spec.seqspec_version)
    barcode = upgraded.library_spec[0].get_region_by_region_type("barcode")[0]
    umi = upgraded.library_spec[0].get_region_by_region_type("umi")[0]
    cdna = next(
        region
        for library in upgraded.library_spec
        for region in library.get_region_by_region_type("cdna")
    )

    assert barcode.region_type == ["RGN:partition:cell"]
    assert region_type_terms(umi.region_type) == {"RGN:partition:molecule"}
    assert region_type_terms(cdna.region_type) == {"RGN:measure:transcript"}
    assert upgraded.library_spec[2].region_type == ["RGN:unknown:unclassified"]


def test_seqspec_upgrade_preserves_index_outputs_for_real_spec():
    spec = load_spec(Path("tests/fixtures/spec.yaml"), strict=False)
    upgraded = seqspec_upgrade(spec.model_copy(deep=True), spec.seqspec_version)

    for tool in ["kb", "simpleaf", "starsolo", "fgbio", "tab"]:
        old = format_index(seqspec_index(spec, "rna", None, "read"), tool, None)
        new = format_index(seqspec_index(upgraded, "rna", None, "read"), tool, None)
        assert new == old

    assert (
        format_index(seqspec_index(upgraded, "rna", ["rna_R1", "rna_R2"], "read"), "fgbio")
        == "16C12M 102T"
    )


def test_seqspec_upgrade_keeps_region_type_queries_backward_compatible():
    spec = load_spec(Path("tests/fixtures/onlist_issue_68/spec.yaml"), strict=False)
    upgraded = seqspec_upgrade(spec.model_copy(deep=True), spec.seqspec_version)

    legacy_find = seqspec_find(upgraded, "region-type", "rna", "barcode")
    ontology_find = seqspec_find(upgraded, "region-type", "rna", "RGN:partition:cell")
    assert [region.region_id for region in legacy_find] == ["barcode_a", "barcode_b"]
    assert [region.region_id for region in legacy_find] == [
        region.region_id for region in ontology_find
    ]

    legacy_onlists = get_onlists(upgraded, "rna", "region-type", "barcode")
    ontology_onlists = get_onlists(upgraded, "rna", "region-type", "RGN:partition:cell")
    assert [onlist.file_id for onlist in legacy_onlists] == [
        onlist.file_id for onlist in ontology_onlists
    ]


def test_seqspec_upgrade_keeps_file_region_type_queries_backward_compatible():
    spec = load_spec(Path("tests/fixtures/spec.yaml"), strict=False)
    upgraded = seqspec_upgrade(spec.model_copy(deep=True), spec.seqspec_version)

    legacy_files = seqspec_file(upgraded, "rna", ["barcode"], "region-type")
    ontology_files = seqspec_file(upgraded, "rna", ["RGN:partition:cell"], "region-type")
    assert sorted(legacy_files) == sorted(ontology_files)
    assert "rna_cell_bc" in ontology_files
    assert ontology_files["rna_cell_bc"][0].file_id == "RNA-737K-arc-v1.txt"


def test_seqspec_upgrade_keeps_seqkit_subregion_queries_backward_compatible():
    spec = load_spec(Path("tests/fixtures/spec.yaml"), strict=False)
    upgraded = seqspec_upgrade(spec.model_copy(deep=True), spec.seqspec_version)
    indices = seqspec_index(upgraded, "rna", ["rna_R1"], "read")

    assert format_index(indices, "seqkit", "RGN:partition:cell") == "1:16\n"
    assert format_index(indices, "seqkit", "barcode") == "1:16\n"


def test_seqspec_upgrade_output_passes_schema_with_region_type_lists():
    spec = load_spec(Path("tests/fixtures/spec.yaml"), strict=False)
    upgraded = seqspec_upgrade(spec.model_copy(deep=True), spec.seqspec_version)

    diagnostics = seqspec_check(upgraded, filter_type="igvf_onlist_skip")

    assert not any(
        diagnostic["severity"] == "error"
        and diagnostic["error_type"] == "check_schema"
        for diagnostic in diagnostics
    )


def test_seqspec_upgrade_yaml_roundtrip_preserves_region_type_lists(tmp_path):
    spec = load_spec(Path("tests/fixtures/spec.yaml"), strict=False)
    upgraded = seqspec_upgrade(spec.model_copy(deep=True), spec.seqspec_version)
    out = tmp_path / "upgraded.yaml"

    upgraded.to_YAML(out)
    serialized = out.read_text()
    serialized_data = yaml.safe_load(serialized)
    reloaded = load_spec(out)

    assert "!!python" not in serialized
    assert (
        serialized_data["library_spec"][2]["regions"][1]["region_type"]
        == ["RGN:partition:cell"]
    )
    assert reloaded.seqspec_version == "0.5.0"
    assert (
        reloaded.get_libspec("rna")
        .get_region_by_region_type("RGN:partition:cell")[0]
        .region_id
        == "rna_cell_bc"
    )
    assert (
        format_index(seqspec_index(reloaded, "rna", ["rna_R1", "rna_R2"], "read"), "fgbio")
        == "16C12M 102T"
    )

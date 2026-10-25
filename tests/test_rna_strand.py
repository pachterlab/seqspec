from pathlib import Path

import pytest
import yaml

from seqspec.Region import RegionInput
from seqspec.seqspec_check import seqspec_check
from seqspec.seqspec_info import format_info, seqspec_info
from seqspec.seqspec_modify import seqspec_modify_region
from seqspec.utils import get_read_rna_strand, load_spec, map_read_id_to_rna_strands

FIXTURE = Path("tests/fixtures/rna_strand/spec.yaml")


@pytest.fixture
def spec():
    return load_spec(FIXTURE)


def region(spec, region_id):
    return spec.get_libspec("rna").get_region_by_id(region_id)[0]


def rna_strand_warnings(spec):
    return [
        d
        for d in seqspec_check(spec=spec, filter_type="external")
        if d["error_type"] == "check_rna_strand"
    ]


def test_load_reads_rna_strand(spec):
    assert region(spec, "cdna").rna_strand == "antisense"
    assert region(spec, "barcode").rna_strand is None


def test_unset_rna_strand_is_not_written(spec):
    dumped = spec.model_dump(mode="json")
    rna = dumped["library_spec"][0]
    assert "rna_strand" not in rna
    leaves = {r["region_id"]: r for r in rna["regions"]}
    assert "rna_strand" not in leaves["barcode"]
    assert leaves["cdna"]["rna_strand"] == "antisense"


def test_yaml_roundtrip_keeps_rna_strand(spec, tmp_path):
    out = tmp_path / "spec.yaml"
    spec.to_YAML(out)
    assert region(load_spec(out), "cdna").rna_strand == "antisense"
    assert yaml.safe_load(out.read_text())["library_spec"][0].get("rna_strand") is None


@pytest.mark.parametrize(
    "rna_strand, read_strand, expected",
    [
        ("sense", "pos", "sense"),
        ("sense", "neg", "antisense"),
        ("antisense", "pos", "antisense"),
        ("antisense", "neg", "sense"),
        ("unstranded", "pos", "unstranded"),
        ("unstranded", "neg", "unstranded"),
        (None, "neg", None),
    ],
)
def test_get_read_rna_strand_truth_table(spec, rna_strand, read_strand, expected):
    region(spec, "cdna").rna_strand = rna_strand
    spec.get_read("rna_R2").strand = read_strand
    # flip the primer side so the read still faces the cDNA
    if read_strand == "pos":
        spec.get_read("rna_R2").primer_id = "umi"
    assert get_read_rna_strand(spec, "rna", "rna_R2") == expected


def test_read_without_rna_region_is_unknown(spec):
    _, strands = map_read_id_to_rna_strands(spec, "rna", "rna_R1")
    assert strands == []
    assert get_read_rna_strand(spec, "rna", "rna_R1") is None


def test_rna_strand_is_inherited_and_overridden(spec):
    libspec = spec.get_libspec("rna")
    region(spec, "cdna").rna_strand = None
    libspec.rna_strand = "sense"
    assert libspec.get_effective_rna_strand("cdna") == "sense"
    assert get_read_rna_strand(spec, "rna", "rna_R2") == "antisense"

    region(spec, "cdna").rna_strand = "unstranded"
    assert libspec.get_effective_rna_strand("cdna") == "unstranded"
    assert get_read_rna_strand(spec, "rna", "rna_R2") == "unstranded"


def test_fixture_has_no_rna_strand_warnings(spec):
    assert rna_strand_warnings(spec) == []


def test_check_warns_when_rna_strand_has_no_effect(spec):
    region(spec, "barcode").rna_strand = "sense"
    warnings = rna_strand_warnings(spec)
    assert len(warnings) == 1
    assert warnings[0]["severity"] == "warning"
    assert warnings[0]["error_object"] == "region"
    assert "'barcode' sets rna_strand" in warnings[0]["error_message"]


def test_check_warns_on_conflicting_rna_strand(spec):
    # split the cDNA into two leaves that disagree, both covered by R2
    libspec = spec.get_libspec("rna")
    cdna = region(spec, "cdna")
    first = cdna.model_copy(deep=True)
    second = cdna.model_copy(deep=True)
    first.region_id, first.min_len, first.max_len, first.sequence = "cdna_a", 2, 2, "XX"
    second.region_id, second.min_len, second.max_len, second.sequence = (
        "cdna_b",
        6,
        6,
        "X" * 6,
    )
    second.rna_strand = "sense"
    idx = libspec.regions.index(cdna)
    libspec.regions[idx : idx + 1] = [first, second]

    warnings = rna_strand_warnings(spec)
    assert len(warnings) == 1
    assert warnings[0]["error_object"] == "read"
    assert "read 'rna_R2'" in warnings[0]["error_message"]
    assert "'cdna_b' (sense)" in warnings[0]["error_message"]
    assert "'cdna_a' (antisense)" in warnings[0]["error_message"]
    assert get_read_rna_strand(spec, "rna", "rna_R2") is None


def test_check_rejects_invalid_rna_strand_value(spec):
    region(spec, "cdna").rna_strand = "forward"
    diagnostics = seqspec_check(spec=spec, filter_type="external")
    assert any(
        d["error_type"] == "check_schema" and "forward" in d["error_message"]
        for d in diagnostics
    )


def test_modify_sets_and_clears_rna_strand(spec):
    spec = seqspec_modify_region(
        spec, "rna", [RegionInput(region_id="cdna", rna_strand="sense")]
    )
    assert region(spec, "cdna").rna_strand == "sense"

    # a patch that does not mention rna_strand leaves it alone
    spec = seqspec_modify_region(spec, "rna", [RegionInput(region_id="cdna", name="x")])
    assert region(spec, "cdna").rna_strand == "sense"

    spec = seqspec_modify_region(
        spec, "rna", [RegionInput(region_id="cdna", rna_strand=None)]
    )
    assert region(spec, "cdna").rna_strand is None


def test_region_input_carries_rna_strand():
    rgn = RegionInput(
        region_id="cdna", region_type="cdna", rna_strand="antisense"
    ).to_region()
    assert rgn.rna_strand == "antisense"


def test_info_rna_strand(spec):
    info = seqspec_info(spec, "rna_strand")
    assert info["rna_strand"] == [
        {"modality": "rna", "read_id": "rna_R1", "strand": "pos", "rna_strand": None},
        {
            "modality": "rna",
            "read_id": "rna_R2",
            "strand": "neg",
            "rna_strand": "sense",
        },
    ]
    assert format_info(info, "rna_strand", "tab") == (
        "rna\trna_R1\tpos\tunknown\nrna\trna_R2\tneg\tsense"
    )


def test_examples_normalizer_keeps_rna_strand():
    from seqspec.examples_docs import normalize_region_dict

    leaf = {
        "region_id": "cdna",
        "region_type": "cdna",
        "sequence_type": "random",
        "sequence": "X",
        "min_len": 1,
        "max_len": 98,
    }
    assert "rna_strand" not in normalize_region_dict(leaf)
    normalized = normalize_region_dict({**leaf, "rna_strand": "antisense"})
    assert normalized["rna_strand"] == "antisense"
    assert list(normalized)[7:] == ["rna_strand", "onlist", "regions"]


def schema_errors(spec):
    return [
        d
        for d in seqspec_check(spec=spec, filter_type="external")
        if d["error_type"] == "check_schema"
    ]


def set_cdna_length(spec, length):
    # keep the cDNA, its parent, and the read covering it consistent
    cdna = region(spec, "cdna")
    cdna.min_len, cdna.max_len, cdna.sequence = 1, length, "X"
    spec.get_libspec("rna").update_attr()
    spec.get_read("rna_R2").max_len = length


@pytest.mark.parametrize("length", [2049, 4_000_000, 2**30 - 16])
def test_region_length_allows_long_reads(spec, length):
    set_cdna_length(spec, length)
    assert schema_errors(spec) == []


def test_region_length_cap_is_2_to_the_30(spec):
    set_cdna_length(spec, 2**30 + 1)
    assert any(str(2**30) in d["error_message"] for d in schema_errors(spec))

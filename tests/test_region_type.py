from seqspec.region_type import (
    UNKNOWN_REGION_TYPE,
    is_cell_barcode,
    is_feature,
    is_index7,
    is_transcript,
    is_technical_skip,
    region_type_matches,
    region_type_terms,
    region_type_tool_label,
    upgrade_region_type,
)


def test_region_type_matches_legacy_and_ontology_values():
    assert region_type_matches(["RGN:partition:cell"], "barcode")
    assert region_type_matches("barcode", "RGN:partition:cell")
    assert not region_type_matches(["RGN:partition:molecule"], "barcode")
    assert not region_type_matches(
        ["RGN:partition:sample", "RGN:technical:index7"], "barcode"
    )


def test_region_type_upgrade_maps_unknown_legacy_to_unknown_term():
    assert upgrade_region_type("not_curated") == [UNKNOWN_REGION_TYPE]
    assert upgrade_region_type(["index7"]) == [
        "RGN:partition:sample",
        "RGN:technical:index7",
    ]


def test_region_type_terms_and_tool_labels_are_semantic():
    region_type = ["RGN:partition:sample", "RGN:technical:index7"]

    assert region_type_terms(region_type) == set(region_type)
    assert is_index7(region_type)
    assert region_type_tool_label(region_type) == "index7"


def test_region_type_semantic_predicates_accept_legacy_values():
    assert is_cell_barcode("barcode")
    assert is_technical_skip("truseq_read1")


def test_region_type_container_labels_do_not_gain_measure_semantics():
    assert upgrade_region_type("rna") == [UNKNOWN_REGION_TYPE]
    assert not is_transcript("rna")
    assert not is_feature("rna")

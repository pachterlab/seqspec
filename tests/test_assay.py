import pytest
import json
from seqspec.Assay import Assay, Region, Read



def test_load_spec(dogmaseq_dig_spec):
    """
    Test that the spec is loaded correctly
    """
    assert dogmaseq_dig_spec is not None
    assert isinstance(dogmaseq_dig_spec, Assay)
    assert dogmaseq_dig_spec.assay_id.upper() == "DOGMASEQ-DIG"

def test_list_modalities(dogmaseq_dig_spec):
    """
    Test list_modalities method
    """
    expected_modalities = ["RNA", "ATAC", "TAG", "PROTEIN"]
    assert set(m.upper() for m in dogmaseq_dig_spec.list_modalities()) == set(expected_modalities)

def test_get_libspec(dogmaseq_dig_spec):
    """
    Test get_libspec method for all modalities
    """
    for modality in dogmaseq_dig_spec.list_modalities():
        lib_spec = dogmaseq_dig_spec.get_libspec(modality)
        assert isinstance(lib_spec, Region)
        assert lib_spec.region_id == modality

def test_get_seqspec(dogmaseq_dig_spec):
    """
    Test get_seqspec method for all modalities
    """
    for modality in dogmaseq_dig_spec.list_modalities():
        seq_spec = dogmaseq_dig_spec.get_seqspec(modality)
        assert isinstance(seq_spec, list)
        for read in seq_spec:
            assert isinstance(read, Read)
            assert read.modality == modality

def test_get_read(dogmaseq_dig_spec):
    """
    Test get_read method
    """
    read = dogmaseq_dig_spec.get_read("atac_R1")
    assert isinstance(read, Read)
    assert read.read_id == "atac_R1"

    with pytest.raises(IndexError):
        dogmaseq_dig_spec.get_read("non_existent_read")

def test_to_json(dogmaseq_dig_spec):
    """
    Test to_JSON method
    """
    json_output = dogmaseq_dig_spec.to_JSON()
    assert isinstance(json_output, str)
    data = json.loads(json_output)
    assert data["assay_id"] == "DOGMAseq-DIG"


def test_insert_regions(dogmaseq_dig_spec):
    """
    Test inserting regions into a specific modality
    """
    new_region = Region(
        region_id="new_test_region",
        region_type="barcode",
        name="New Test Region",
        sequence_type="fixed",
        sequence="ACGT",
        min_len=4,
        max_len=4,
    )
    modality = "rna"
    original_lib_spec = dogmaseq_dig_spec.get_libspec(modality)
    original_region_count = len(original_lib_spec.regions)

    dogmaseq_dig_spec.insert_regions([new_region], modality)

    updated_lib_spec = dogmaseq_dig_spec.get_libspec(modality)
    assert len(updated_lib_spec.regions) == original_region_count + 1
    assert updated_lib_spec.regions[0].region_id == "new_test_region"

def test_insert_reads(dogmaseq_dig_spec):
    """
    Test inserting reads into the sequence_spec
    """
    new_read = Read(
        read_id="new_test_read",
        name="New Test Read",
        modality="atac",
        primer_id="some_primer",
        min_len=50,
        max_len=50,
        strand="pos",
    )
    modality = "atac"
    original_read_count = len(dogmaseq_dig_spec.sequence_spec)
    original_modality_read_count = len(dogmaseq_dig_spec.get_seqspec(modality))

    dogmaseq_dig_spec.insert_reads([new_read], modality)

    assert len(dogmaseq_dig_spec.sequence_spec) == original_read_count + 1
    assert (
        len(dogmaseq_dig_spec.get_seqspec(modality))
        == original_modality_read_count + 1
    )
    assert dogmaseq_dig_spec.sequence_spec[0].read_id == "new_test_read"

def test_update_spec(dogmaseq_dig_spec):
    """
    Test update_spec method to ensure sequences and lengths are recalculated
    """
    modality = "rna"
    lib_spec = dogmaseq_dig_spec.get_libspec(modality)

    # Get original sequence and lengths
    original_sequence = lib_spec.sequence
    original_min_len = lib_spec.min_len
    original_max_len = lib_spec.max_len

    # Modify a sub-region
    # Making sure there are regions to modify
    if lib_spec.regions:
        sub_region = lib_spec.regions[0]
        sub_region.sequence = "TTTT"
        sub_region.min_len = 4
        sub_region.max_len = 4

        # Update the spec
        dogmaseq_dig_spec.update_spec()

        # Check if the parent region's attributes are updated
        updated_lib_spec = dogmaseq_dig_spec.get_libspec(modality)
        assert updated_lib_spec.sequence != original_sequence
    else:
        pytest.skip(f"No regions to modify for modality {modality}")

def test_print_sequence(dogmaseq_dig_spec, capsys):
    """
    Test the print_sequence method
    """
    dogmaseq_dig_spec.print_sequence()
    captured = capsys.readouterr()
    assert captured.out is not None and len(captured.out.strip()) > 0

    # Check that the output contains concatenated sequences from the library_spec
    expected_sequence = ""
    for region in dogmaseq_dig_spec.library_spec:
        expected_sequence += region.get_sequence()
    expected_sequence += "\n"

    assert captured.out == expected_sequence

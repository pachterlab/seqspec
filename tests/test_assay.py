import pytest
import json
from seqspec.Assay import Assay, Region, Read
from seqspec.Assay import Assay, RustAssay, SeqProtocol, SeqKit, LibProtocol, LibKit
from seqspec.Read import ReadInput
from seqspec.Region import RegionInput


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


def test_insert_regions(temp_spec):
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
    original_lib_spec = temp_spec.get_libspec(modality)
    original_region_count = len(original_lib_spec.regions)

    temp_spec.insert_regions([new_region], modality)

    updated_lib_spec = temp_spec.get_libspec(modality)
    assert len(updated_lib_spec.regions) == original_region_count + 1
    assert updated_lib_spec.regions[0].region_id == "new_test_region"

def test_insert_reads(temp_spec):
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
    original_read_count = len(temp_spec.sequence_spec)
    original_modality_read_count = len(temp_spec.get_seqspec(modality))

    temp_spec.insert_reads([new_read], modality)

    assert len(temp_spec.sequence_spec) == original_read_count + 1
    assert (
        len(temp_spec.get_seqspec(modality))
        == original_modality_read_count + 1
    )
    assert temp_spec.sequence_spec[0].read_id == "new_test_read"

def test_update_spec(temp_spec):
    """
    Test update_spec method to ensure sequences and lengths are recalculated
    """
    modality = "rna"
    lib_spec = temp_spec.get_libspec(modality)

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
        temp_spec.update_spec()

        # Check if the parent region's attributes are updated
        updated_lib_spec = temp_spec.get_libspec(modality)
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

def test_assay_kits_protocols_list_only(dogmaseq_dig_spec: Assay):
    pytest.importorskip("seqspec._core")

    # Start from an existing spec and add lists of objects
    spec = dogmaseq_dig_spec.model_copy(deep=True)
    spec.sequence_protocol = [SeqProtocol(protocol_id="NovaSeq", name="Illumina NovaSeq", modality=spec.modalities[0])]
    spec.sequence_kit = [SeqKit(kit_id="NovaKit", name="NovaSeq v1.5", modality=spec.modalities[0])]
    spec.library_protocol = [LibProtocol(protocol_id="10x_rna", name="10x RNA", modality=spec.modalities[0])]
    spec.library_kit = [LibKit(kit_id="TruSeq", name="TruSeq Dual", modality=spec.modalities[0])]

    ra = RustAssay.from_model(spec)
    snap = ra.snapshot()

    assert isinstance(snap.sequence_protocol, list)
    assert getattr(snap.sequence_protocol[0], "protocol_id", None) == "NovaSeq"
    assert isinstance(snap.sequence_kit, list)
    assert getattr(snap.sequence_kit[0], "kit_id", None) == "NovaKit"
    assert isinstance(snap.library_protocol, list)
    assert getattr(snap.library_protocol[0], "name", None) == "10x RNA"
    assert isinstance(snap.library_kit, list)
    assert getattr(snap.library_kit[0], "name", None) == "TruSeq Dual"


def test_rustassay_snapshot_and_modalities_parity(dogmaseq_dig_spec: Assay):
    pytest.importorskip("seqspec._core")

    py = dogmaseq_dig_spec
    ra = RustAssay.from_model(py)
    snap = ra.snapshot()

    # Whole-object parity (JSON) and modalities
    assert snap.model_dump_json() == py.model_dump_json()
    assert ra.list_modalities() == py.list_modalities()

    # __repr__ parity (structural depiction)
    assert repr(snap) == repr(py)


def test_rustassay_getters_parity(dogmaseq_dig_spec: Assay):
    pytest.importorskip("seqspec._core")
    py = dogmaseq_dig_spec
    ra = RustAssay.from_model(py)

    # get_libspec parity (compare DTO json per modality)
    for m in py.list_modalities():
        py_lib = py.get_libspec(m)
        ru_lib = ra.get_libspec(m)
        assert ru_lib.model_dump_json() == py_lib.model_dump_json()

    # get_seqspec parity
    for m in py.list_modalities():
        py_reads = py.get_seqspec(m)
        ru_reads = ra.get_seqspec(m)
        assert len(py_reads) == len(ru_reads)
        for pr, rr in zip(py_reads, ru_reads):
            assert rr.model_dump_json() == pr.model_dump_json()

    # get_read parity
    # choose a known read id from the spec
    known = py.sequence_spec[0].read_id
    assert ra.get_read(known).model_dump_json() == py.get_read(known).model_dump_json()


def test_rustassay_insert_reads_regions_parity(temp_spec: Assay):
    pytest.importorskip("seqspec._core")

    # Work on a copy to avoid mutating fixtures
    py = temp_spec.model_copy(deep=True)
    ra = RustAssay.from_model(py)

    # Prepare a new read and region
    new_read = Read(
        read_id="new_RX",
        name="New Read X",
        modality="rna",
        primer_id="primerX",
        min_len=42,
        max_len=42,
        strand="pos",
    )
    new_region = Region(
        region_id="new_regX",
        region_type="named",
        name="new_regX",
        sequence_type="fixed",
        sequence="ACGT",
        min_len=4,
        max_len=4,
        regions=[],
    )

    # Insert in Python
    py.insert_reads([new_read], modality="rna")
    py.insert_regions([new_region], modality="rna")

    # Insert in Rust and snapshot
    ra.insert_reads([new_read], modality="rna")
    ra.insert_regions([new_region], modality="rna")
    snap = ra.snapshot()

    # Full object parity after inserts
    assert snap.model_dump_json() == py.model_dump_json()


def test_rustassay_update_spec_parity(temp_spec: Assay):
    pytest.importorskip("seqspec._core")

    py = temp_spec.model_copy(deep=True)
    ra = RustAssay.from_model(py)

    # Trigger updates on both sides
    py.update_spec()
    ra.update_spec()
    snap = ra.snapshot()

    # Parity after update (derived attributes on regions recomputed)
    assert snap.model_dump_json() == py.model_dump_json()
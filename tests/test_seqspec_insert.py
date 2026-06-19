from seqspec.seqspec_insert import (
    load_resource_payload,
    seqspec_insert_reads,
    seqspec_insert_regions,
)
from seqspec.Assay import Assay
from seqspec.Read import ReadInput
from seqspec.Region import RegionInput
from typing import Any, List


def test_seqspec_insert_reads(temp_spec):
    """Test inserting reads into a spec"""
    # Create test reads
    new_reads = [
        ReadInput(
            read_id="test_R1",
            name="Test Read 1",
            modality="rna",
            primer_id="test_primer",
            min_len=50,
            max_len=50,
            strand="pos",
        ),
        ReadInput(
            read_id="test_R2",
            name="Test Read 2",
            modality="rna",
            primer_id="test_primer",
            min_len=50,
            max_len=50,
            strand="neg",
        ),
    ]
    
    # Get original read count
    original_read_count = len(temp_spec.sequence_spec)
    original_rna_read_count = len(temp_spec.get_seqspec("rna"))
    
    # Insert reads
    updated_spec = seqspec_insert_reads(temp_spec, "rna", new_reads)
    
    # Check that reads were added
    assert len(updated_spec.sequence_spec) == original_read_count + 2
    assert len(updated_spec.get_seqspec("rna")) == original_rna_read_count + 2
    
    # Check that the new reads are present
    read_ids = [read.read_id for read in updated_spec.sequence_spec]
    assert "test_R1" in read_ids
    assert "test_R2" in read_ids


def test_seqspec_insert_reads_after_specific_read(temp_spec):
    """Test inserting reads after a specific read"""
    # Create a test read
    new_read = ReadInput(
        read_id="inserted_read",
        name="Inserted Read",
        modality="rna",
        primer_id="test_primer",
        min_len=50,
        max_len=50,
        strand="pos",
    )
    
    # Get original RNA reads
    original_rna_reads = temp_spec.get_seqspec("rna")
    original_read_ids = [read.read_id for read in original_rna_reads]
    
    # Insert after the first RNA read
    target_read_id = original_rna_reads[0].read_id
    updated_spec = seqspec_insert_reads(temp_spec, "rna", [new_read], after=target_read_id)
    
    # Check that the read was inserted in the correct position
    updated_rna_reads = updated_spec.get_seqspec("rna")
    updated_read_ids = [read.read_id for read in updated_rna_reads]
    
    # Find the position of the inserted read
    inserted_index = updated_read_ids.index("inserted_read")
    target_index = updated_read_ids.index(target_read_id)
    
    # The inserted read should come right after the target read
    assert inserted_index == target_index + 1


def test_seqspec_insert_regions(temp_spec):
    """Test inserting regions into a spec"""
    # Create test regions
    new_regions = [
        RegionInput(
            region_id="test_region_1",
            region_type="barcode",
            name="Test Region 1",
            sequence_type="fixed",
            sequence="ACGT",
            min_len=4,
            max_len=4,
        ),
        RegionInput(
            region_id="test_region_2",
            region_type="umi",
            name="Test Region 2",
            sequence_type="random",
            sequence="XXXX",
            min_len=4,
            max_len=4,
        ),
    ]
    
    # Get original region count for RNA modality
    original_rna_lib_spec = temp_spec.get_libspec("rna")
    original_region_count = len(original_rna_lib_spec.regions)
    
    # Insert regions
    updated_spec = seqspec_insert_regions(temp_spec, "rna", new_regions)
    
    # Check that regions were added
    updated_rna_lib_spec = updated_spec.get_libspec("rna")
    assert len(updated_rna_lib_spec.regions) == original_region_count + 2
    
    # Check that the new regions are present
    region_ids = [region.region_id for region in updated_rna_lib_spec.regions]
    assert "test_region_1" in region_ids
    assert "test_region_2" in region_ids


def test_seqspec_insert_region_accepts_region_type_list(temp_spec):
    """Test inserting ontology-list region types into a spec."""
    new_region = RegionInput(
        region_id="test_sample_index",
        region_type=["RGN:partition:sample", "RGN:technical:index7"],
        name="Test Sample Index",
        sequence_type="onlist",
        sequence="NNNN",
        min_len=4,
        max_len=4,
    )

    updated_spec = seqspec_insert_regions(temp_spec, "rna", [new_region])

    region = updated_spec.get_libspec("rna").get_region_by_id("test_sample_index")[0]
    assert region.region_type == ["RGN:partition:sample", "RGN:technical:index7"]
    assert region.get_region_by_region_type("index7")[0].region_id == "test_sample_index"


def test_seqspec_insert_regions_after_specific_region(temp_spec):
    """Test inserting regions after a specific region"""
    # Create a test region
    new_region = RegionInput(
        region_id="inserted_region",
        region_type="linker",
        name="Inserted Region",
        sequence_type="fixed",
        sequence="TTTT",
        min_len=4,
        max_len=4,
    )
    
    # Get original RNA library spec
    original_rna_lib_spec = temp_spec.get_libspec("rna")
    original_region_ids = [region.region_id for region in original_rna_lib_spec.regions]
    
    # Insert after the first region
    target_region_id = original_rna_lib_spec.regions[0].region_id
    updated_spec = seqspec_insert_regions(temp_spec, "rna", [new_region], after=target_region_id)
    
    # Check that the region was inserted in the correct position
    updated_rna_lib_spec = updated_spec.get_libspec("rna")
    updated_region_ids = [region.region_id for region in updated_rna_lib_spec.regions]
    
    # Find the position of the inserted region
    inserted_index = updated_region_ids.index("inserted_region")
    target_index = updated_region_ids.index(target_region_id)
    
    # The inserted region should come right after the target region
    assert inserted_index == target_index + 1


def test_seqspec_insert_reads_different_modality(temp_spec):
    """Test inserting reads into a different modality"""
    # Create test reads for ATAC modality
    new_reads = [
        ReadInput(
            read_id="atac_test_R1",
            name="ATAC Test Read 1",
            modality="atac",
            primer_id="atac_test_primer",
            min_len=50,
            max_len=50,
            strand="pos",
        )
    ]
    
    # Get original ATAC read count
    original_atac_read_count = len(temp_spec.get_seqspec("atac"))
    
    # Insert reads into ATAC modality
    updated_spec = seqspec_insert_reads(temp_spec, "atac", new_reads)
    
    # Check that reads were added to ATAC modality
    assert len(updated_spec.get_seqspec("atac")) == original_atac_read_count + 1
    
    # Check that the new read is present
    atac_read_ids = [read.read_id for read in updated_spec.get_seqspec("atac")]
    assert "atac_test_R1" in atac_read_ids


def test_seqspec_insert_regions_different_modality(temp_spec):
    """Test inserting regions into a different modality"""
    # Create test region for protein modality
    new_region = RegionInput(
        region_id="protein_test_region",
        region_type="barcode",
        name="Protein Test Region",
        sequence_type="fixed",
        sequence="GCTA",
        min_len=4,
        max_len=4,
    )
    
    # Get original protein region count
    original_protein_lib_spec = temp_spec.get_libspec("protein")
    original_region_count = len(original_protein_lib_spec.regions)
    
    # Insert region into protein modality
    updated_spec = seqspec_insert_regions(temp_spec, "protein", [new_region])
    
    # Check that region was added to protein modality
    updated_protein_lib_spec = updated_spec.get_libspec("protein")
    assert len(updated_protein_lib_spec.regions) == original_region_count + 1
    
    # Check that the new region is present
    protein_region_ids = [region.region_id for region in updated_protein_lib_spec.regions]
    assert "protein_test_region" in protein_region_ids


def test_seqspec_insert_preserves_other_modalities(temp_spec):
    """Test that inserting into one modality doesn't affect others"""
    # Create test read for RNA modality
    new_read = ReadInput(
        read_id="rna_test_read",
        name="RNA Test Read",
        modality="rna",
        primer_id="rna_test_primer",
        min_len=50,
        max_len=50,
        strand="pos",
    )
    
    # Get original read counts for different modalities
    original_rna_count = len(temp_spec.get_seqspec("rna"))
    original_atac_count = len(temp_spec.get_seqspec("atac"))
    original_protein_count = len(temp_spec.get_seqspec("protein"))
    original_tag_count = len(temp_spec.get_seqspec("tag"))
    
    # Insert read into RNA modality
    updated_spec = seqspec_insert_reads(temp_spec, "rna", [new_read])
    
    # Check that only RNA modality was affected
    assert len(updated_spec.get_seqspec("rna")) == original_rna_count + 1
    assert len(updated_spec.get_seqspec("atac")) == original_atac_count
    assert len(updated_spec.get_seqspec("protein")) == original_protein_count
    assert len(updated_spec.get_seqspec("tag")) == original_tag_count 


def test_seqspec_insert_general_read(temp_spec: Assay):
    """Test inserting with ReadInput via direct reads insert API."""
    original_rna_read_count = len(temp_spec.get_seqspec("rna"))

    resources: List[Any] = [
        ReadInput(
            read_id="general_R1",
            name="General Read",
            modality="rna",
            primer_id="rna_cell_bc",
            min_len=10,
            max_len=10,
            strand="pos",
        )
    ]

    updated_spec = seqspec_insert_reads(temp_spec, "rna", resources)

    assert len(updated_spec.get_seqspec("rna")) == original_rna_read_count + 1
    read_ids = [r.read_id for r in updated_spec.get_seqspec("rna")]
    assert "general_R1" in read_ids


def test_load_resource_payload_accepts_yaml_file(tmp_path):
    resource_path = tmp_path / "regions.yaml"
    resource_path.write_text(
        "- region_id: inserted_region\n"
        "  region_type: linker\n"
        "  name: Inserted Region\n"
        "  sequence_type: fixed\n"
        "  sequence: ACGT\n"
        "  min_len: 4\n"
        "  max_len: 4\n"
    )

    payload = load_resource_payload(str(resource_path))

    assert isinstance(payload, list)
    assert payload[0]["region_id"] == "inserted_region"


def test_load_resource_payload_accepts_reads_mapping():
    payload = load_resource_payload(
        '{"reads":[{"read_id":"wrapped_R1","name":"Wrapped Read","primer_id":"rna_polyT","min_len":10,"max_len":10,"strand":"pos"}]}'
    )

    assert isinstance(payload, dict)
    assert payload["reads"][0]["read_id"] == "wrapped_R1"


def test_load_resource_payload_accepts_regions_mapping():
    payload = load_resource_payload(
        '{"regions":[{"region_id":"wrapped_bc","region_type":"barcode","name":"Wrapped Barcode","sequence_type":"fixed","sequence":"ACGT","min_len":4,"max_len":4}]}'
    )

    assert isinstance(payload, dict)
    assert payload["regions"][0]["region_id"] == "wrapped_bc"


def test_seqspec_insert_reads_invalid_modality_raises(temp_spec):
    new_read = ReadInput(
        read_id="bad_read",
        name="Bad Read",
        modality="rna",
        primer_id="test_primer",
        min_len=10,
        max_len=10,
        strand="pos",
    )

    try:
        seqspec_insert_reads(temp_spec, "missing", [new_read])
    except ValueError as exc:
        assert "Modality 'missing' not found." in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid modality")


def test_seqspec_insert_regions_missing_after_raises(temp_spec):
    new_region = RegionInput(
        region_id="bad_region",
        region_type="barcode",
        name="Bad Region",
        sequence_type="fixed",
        sequence="ACGT",
        min_len=4,
        max_len=4,
    )

    try:
        seqspec_insert_regions(temp_spec, "rna", [new_region], after="missing")
    except ValueError as exc:
        assert "No region with id 'missing' found under modality 'rna'" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing insertion target")

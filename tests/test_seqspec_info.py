from seqspec.seqspec_info import seqspec_info, format_info
from seqspec.Assay import Assay
import json


def test_seqspec_info(dogmaseq_dig_spec: Assay):
    # Test getting modalities
    info = seqspec_info(spec=dogmaseq_dig_spec, key="modalities")
    assert "modalities" in info
    assert set(info["modalities"]) == {"protein", "tag", "rna", "atac"}

    # Test getting meta
    info = seqspec_info(spec=dogmaseq_dig_spec, key="meta")
    assert "meta" in info
    assert info["meta"]["assay_id"] == "DOGMAseq-DIG"

    # Test getting sequence_spec
    info = seqspec_info(spec=dogmaseq_dig_spec, key="sequence_spec")
    assert "sequence_spec" in info
    assert len(info["sequence_spec"]) > 0

    # Test getting library_spec
    info = seqspec_info(spec=dogmaseq_dig_spec, key="library_spec")
    assert "library_spec" in info
    assert "rna" in info["library_spec"]


def test_format_info(dogmaseq_dig_spec: Assay):
    # Test formatting modalities
    info = seqspec_info(spec=dogmaseq_dig_spec, key="modalities")
    formatted_info = format_info(info, "modalities", "tab")
    assert "protein\ttag\trna\tatac" in formatted_info

    # Test formatting meta as json
    info = seqspec_info(spec=dogmaseq_dig_spec, key="meta")
    formatted_info = format_info(info, "meta", "json")
    meta_dict = json.loads(formatted_info)
    assert meta_dict["name"] == "DOGMAseq-DIG/Illumina"


def test_seqspec_info_modalities(dogmaseq_dig_spec: Assay):
    """Test seqspec_info with modalities key"""
    info = seqspec_info(spec=dogmaseq_dig_spec, key="modalities")
    assert info == {'modalities': ['protein', 'tag', 'rna', 'atac']}


def test_seqspec_info_sequence_spec(dogmaseq_dig_spec: Assay):
    """Test seqspec_info with sequence_spec key"""
    info = seqspec_info(spec=dogmaseq_dig_spec, key="sequence_spec")
    assert "sequence_spec" in info
    sequence_spec = info["sequence_spec"]

    assert len(sequence_spec) > 0
    
    # Check that we have the expected reads
    read_ids = [read["read_id"] for read in sequence_spec]
    expected_reads = ["protein_R1", "protein_R2", "tag_R1", "tag_R2", "rna_R1", "rna_R2", "atac_R1", "atac_R2", "atac_R3"]
    assert set(read_ids) == set(expected_reads)
    
    # Check structure of first read
    protein_r1 = next(read for read in sequence_spec if read["read_id"] == "protein_R1")
    assert protein_r1["name"] == "protein Read 1"
    assert protein_r1["modality"] == "protein"
    assert protein_r1["min_len"] == 28
    assert protein_r1["max_len"] == 28
    assert protein_r1["strand"] == "pos"


def test_seqspec_info_library_spec(dogmaseq_dig_spec: Assay):
    """Test seqspec_info with library_spec key"""
    info = seqspec_info(spec=dogmaseq_dig_spec, key="library_spec")
    assert "library_spec" in info
    library_spec = info["library_spec"]
    
    # Check that all modalities are present
    assert set(library_spec.keys()) == {"protein", "tag", "rna", "atac"}
    
    # Check protein modality regions
    protein_regions = library_spec["protein"]
    region_ids = [region["region_id"] for region in protein_regions]
    expected_protein_regions = [
        "protein_truseq_read1", "protein_cell_bc",
        "protein_umi", "protein_seq", "protein_truseq_read2"
    ]
    assert set(region_ids) == set(expected_protein_regions)
    
    # Check specific region properties
    protein_cell_bc = next(region for region in protein_regions if region["region_id"] == "protein_cell_bc")
    assert protein_cell_bc["region_type"] == "barcode"
    assert protein_cell_bc["name"] == "Cell Barcode"
    assert protein_cell_bc["min_len"] == 16
    assert protein_cell_bc["max_len"] == 16


def test_seqspec_info_meta(dogmaseq_dig_spec: Assay):
    """Test seqspec_info with meta key"""
    info = seqspec_info(spec=dogmaseq_dig_spec, key="meta")
    assert "meta" in info
    meta = info["meta"]
    
    # Check key metadata fields
    assert meta["assay_id"] == "DOGMAseq-DIG"
    assert meta["name"] == "DOGMAseq-DIG/Illumina"
    assert "description" in meta
    assert "seqspec_version" in meta
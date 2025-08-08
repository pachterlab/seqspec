from seqspec.seqspec_index import seqspec_index, format_index
from seqspec.Assay import Assay
from seqspec.Region import RegionCoordinate
import json


def test_seqspec_index(dogmaseq_dig_spec: Assay):
    # Test get_index_by_read_ids
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="rna", ids=["rna_R1"], idtype="read"
    )
    assert len(indices) == 1
    assert "rna_R1" in indices[0]
    assert indices[0]["strand"] == "pos"

    # Test get_index_by_file_ids
    indices = seqspec_index(
        spec=dogmaseq_dig_spec,
        modality="rna",
        ids=["rna_R1_SRR18677638.fastq.gz"],
        idtype="file",
    )

    # Check that indices match the expected structure and values
    assert len(indices) == 1
    index = indices[0]
    assert "rna_R1" in index
    assert index["strand"] == "pos"
    regions = index["rna_R1"]
    assert len(regions) == 2

    # Check that regions are RegionCoordinate objects
    assert all(isinstance(region, RegionCoordinate) for region in regions)

    cell_bc = regions[0]
    umi = regions[1]

    # Check cell barcode region
    assert cell_bc.region_id == "rna_cell_bc"
    assert cell_bc.region_type == "barcode"
    assert cell_bc.name == "Cell Barcode"
    assert cell_bc.sequence_type == "onlist"
    assert cell_bc.sequence == "NNNNNNNNNNNNNNNN"
    assert cell_bc.min_len == 16
    assert cell_bc.max_len == 16
    assert cell_bc.start == 0
    assert cell_bc.stop == 16
    assert cell_bc.onlist is not None
    assert cell_bc.onlist.file_id == "RNA-737K-arc-v1.txt"
    assert cell_bc.onlist.filename == "RNA-737K-arc-v1.txt"
    assert cell_bc.onlist.filetype == "txt"
    assert cell_bc.onlist.filesize == 2142553
    assert cell_bc.onlist.url == "https://github.com/pachterlab/qcbc/raw/main/tests/10xMOME/RNA-737K-arc-v1.txt.gz"
    assert cell_bc.onlist.urltype == "https"
    assert cell_bc.onlist.md5 == "a88cd21e801ae6f9a7d9a48b67ccf693"
    assert cell_bc.regions == []

    # Check UMI region
    assert umi.region_id == "rna_umi"
    assert umi.region_type == "umi"
    assert umi.name == "umi"
    assert umi.sequence_type == "random"
    assert umi.sequence == "XXXXXXXXXXXX"
    assert umi.min_len == 12
    assert umi.max_len == 12
    assert umi.start == 16
    assert umi.stop == 28
    assert umi.onlist is None
    assert umi.regions == []

    # Test get_index_by_region_ids
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="rna", ids=["rna_umi"], idtype="region"
    )
    assert len(indices) == 1


def test_seqspec_index_without_ids(dogmaseq_dig_spec: Assay):
    """Test seqspec_index without providing ids (uses get_index_by_files)"""
    # Test file indexing without specific IDs
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="rna", ids=[], idtype="file"
    )
    
    # Should return indices for all files in the modality
    assert len(indices) > 0
    
    # Check structure of returned indices
    for index in indices:
        assert isinstance(index, dict)
        assert "strand" in index
        # Should have at least one read ID as key
        read_keys = [k for k in index.keys() if k != "strand"]
        assert len(read_keys) > 0
        
        # Check that the regions are RegionCoordinate objects
        for read_id in read_keys:
            regions = index[read_id]
            assert isinstance(regions, list)
            assert all(isinstance(region, RegionCoordinate) for region in regions)


def test_seqspec_index_multiple_read_ids(dogmaseq_dig_spec: Assay):
    """Test seqspec_index with multiple read IDs"""
    # Test multiple read IDs for RNA modality
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, 
        modality="rna", 
        ids=["rna_R1", "rna_R2"], 
        idtype="read"
    )
    
    assert len(indices) == 2
    
    # Check first read (rna_R1)
    rna_r1_index = indices[0]
    assert "rna_R1" in rna_r1_index
    assert rna_r1_index["strand"] == "pos"
    rna_r1_regions = rna_r1_index["rna_R1"]
    assert len(rna_r1_regions) == 2  # cell_bc + umi
    
    # Check second read (rna_R2) - this has negative strand
    rna_r2_index = indices[1]
    assert "rna_R2" in rna_r2_index
    assert rna_r2_index["strand"] == "neg"  # Fixed: rna_R2 has negative strand
    rna_r2_regions = rna_r2_index["rna_R2"]
    assert len(rna_r2_regions) == 1  # cdna only


def test_seqspec_index_multiple_file_ids(dogmaseq_dig_spec: Assay):
    """Test seqspec_index with multiple file IDs"""
    # Test multiple file IDs for RNA modality
    indices = seqspec_index(
        spec=dogmaseq_dig_spec,
        modality="rna",
        ids=["rna_R1_SRR18677638.fastq.gz", "rna_R2_SRR18677638.fastq.gz"],
        idtype="file"
    )
    
    assert len(indices) == 2
    
    # Check that each index corresponds to a read
    for index in indices:
        assert isinstance(index, dict)
        assert "strand" in index
        read_keys = [k for k in index.keys() if k != "strand"]
        assert len(read_keys) == 1
        
        # Check that regions are RegionCoordinate objects
        for read_id in read_keys:
            regions = index[read_id]
            assert all(isinstance(region, RegionCoordinate) for region in regions)


def test_seqspec_index_multiple_region_ids(dogmaseq_dig_spec: Assay):
    """Test seqspec_index with multiple region IDs"""
    # Test multiple region IDs for RNA modality
    indices = seqspec_index(
        spec=dogmaseq_dig_spec,
        modality="rna",
        ids=["rna_cell_bc", "cdna"],  # Use region IDs
        idtype="region"
    )
    
    assert len(indices) == 2
    
    # Check that each index has the expected structure
    for index in indices:
        assert isinstance(index, dict)
        assert "strand" in index
        region_keys = [k for k in index.keys() if k != "strand"]
        assert len(region_keys) == 1
        
        # Check that regions are RegionCoordinate objects
        for region_id in region_keys:
            regions = index[region_id]
            assert all(isinstance(region, RegionCoordinate) for region in regions)


def test_seqspec_index_different_modalities(dogmaseq_dig_spec: Assay):
    """Test seqspec_index across different modalities"""
    # Test RNA modality
    rna_indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="rna", ids=["rna_R1"], idtype="read"
    )
    assert len(rna_indices) == 1
    assert "rna_R1" in rna_indices[0]
    
    # Test ATAC modality
    atac_indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="atac", ids=["atac_R1"], idtype="read"
    )
    assert len(atac_indices) == 1
    assert "atac_R1" in atac_indices[0]
    
    # Test protein modality
    protein_indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="protein", ids=["protein_R1"], idtype="read"
    )
    assert len(protein_indices) == 1
    assert "protein_R1" in protein_indices[0]
    
    # Test tag modality
    tag_indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="tag", ids=["tag_R1"], idtype="read"
    )
    assert len(tag_indices) == 1
    assert "tag_R1" in tag_indices[0]


def test_seqspec_index_reverse_strand(dogmaseq_dig_spec: Assay):
    """Test seqspec_index with reverse strand ordering"""
    # Test with rev=True
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, 
        modality="rna", 
        ids=["rna_R1"], 
        idtype="read",
        rev=True
    )
    
    assert len(indices) == 1
    assert "rna_R1" in indices[0]
    assert indices[0]["strand"] == "pos"  # Strand should still be pos for this read
    
    # Check that regions are still RegionCoordinate objects
    regions = indices[0]["rna_R1"]
    assert all(isinstance(region, RegionCoordinate) for region in regions)


def test_seqspec_index_edge_cases(dogmaseq_dig_spec: Assay):
    """Test seqspec_index with edge cases"""
    # Test with empty ids list for file type (this should work)
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="rna", ids=[], idtype="file"
    )
    # This should return indices for all files in the modality
    assert isinstance(indices, list)
    assert len(indices) > 0
    
    # Test with empty ids list for read type (should raise KeyError)
    try:
        indices = seqspec_index(
            spec=dogmaseq_dig_spec, modality="rna", ids=[], idtype="read"
        )
        # If we get here, it means the function handles empty IDs gracefully
        assert isinstance(indices, list)
    except KeyError:
        # This is expected behavior - read type requires IDs
        pass
    
    # Test with empty ids list for region type (should raise KeyError)
    try:
        indices = seqspec_index(
            spec=dogmaseq_dig_spec, modality="rna", ids=[], idtype="region"
        )
        # If we get here, it means the function handles empty IDs gracefully
        assert isinstance(indices, list)
    except KeyError:
        # This is expected behavior - region type requires IDs
        pass


def test_seqspec_index_structure_validation(dogmaseq_dig_spec: Assay):
    """Test that seqspec_index returns properly structured data"""
    # Test all idtypes to ensure consistent structure
    idtypes = ["read", "region", "file"]
    
    for idtype in idtypes:
        if idtype == "read":
            ids = ["rna_R1"]
        elif idtype == "region":
            ids = ["rna_cell_bc"]
        else:  # file
            ids = ["rna_R1_SRR18677638.fastq.gz"]
        
        indices = seqspec_index(
            spec=dogmaseq_dig_spec, modality="rna", ids=ids, idtype=idtype
        )
        
        # Validate structure
        assert isinstance(indices, list)
        assert len(indices) > 0
        
        for index in indices:
            assert isinstance(index, dict)
            assert "strand" in index
            assert index["strand"] in ["pos", "neg"]
            
            # Should have at least one key that's not "strand"
            data_keys = [k for k in index.keys() if k != "strand"]
            assert len(data_keys) > 0
            
            # Check that the data contains RegionCoordinate objects
            for key in data_keys:
                regions = index[key]
                assert isinstance(regions, list)
                assert all(isinstance(region, RegionCoordinate) for region in regions)


def test_format_index():
    """Test format_index with various formats"""
    from seqspec.utils import load_spec
    
    # Load fresh spec to avoid state interference
    dogmaseq_dig_spec = load_spec("tests/fixtures/spec.yaml")
    
    # Test tab format for RNA
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="rna", ids=["rna_R1"], idtype="read"
    )
    formatted_index = format_index(indices, "tab")
    expected_rna_tab = "rna_R1\tCell Barcode\tbarcode\t0\t16\nrna_R1\tumi\tumi\t16\t28"
    assert formatted_index == expected_rna_tab

    # Test tab format for tag modality
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="tag", ids=["tag_R1", "tag_R2"], idtype="read"
    )
    formatted_index = format_index(indices, "tab")
    expected_tag_tab = "tag_R1\tCell Barcode\tbarcode\t0\t16\ntag_R1\tumi\tumi\t16\t28\ntag_R2\ttag sequence\ttag\t0\t15"
    assert formatted_index == expected_tag_tab

    # Test kallisto bus format
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="rna", ids=["rna_R1", "rna_R2"], idtype="read"
    )
    formatted_index = format_index(indices, "kb")
    expected_kb = "0,0,16:0,16,28:1,0,102"
    assert formatted_index == expected_kb

    # Test chromap format for ATAC
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="atac", ids=["atac_R1", "atac_R2", "atac_R3"], idtype="read"
    )
    formatted_index = format_index(indices, "chromap")
    expected_chromap = "-1 atac_R1 -2 atac_R3 --barcode atac_R2 --read-format bc:8:23,r1:0:52,r2:0:52"
    assert formatted_index == expected_chromap

    # Test simpleaf format for protein
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="protein", ids=["protein_R1", "protein_R2"], idtype="read"
    )
    formatted_index = format_index(indices, "simpleaf")
    expected_simpleaf = "1{b[16]u[12]x:}2{x:}"
    assert formatted_index == expected_simpleaf

    # Test starsolo format for protein
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="protein", ids=["protein_R1", "protein_R2"], idtype="read"
    )
    formatted_index = format_index(indices, "starsolo")
    expected_starsolo = "--soloType CB_UMI_Simple --soloCBstart 1 --soloCBlen 16 --soloUMIstart 17 --soloUMIlen 12"
    assert formatted_index == expected_starsolo

    # Test zumis format for RNA
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="rna", ids=["rna_R1", "rna_R2"], idtype="read"
    )
    formatted_index = format_index(indices, "zumis")
    expected_zumis = "- BCS(1-16)\n- UMI(17-28)\n\n- cDNA(1-102)"
    assert formatted_index == expected_zumis

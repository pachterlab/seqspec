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
    assert "rna_R1" == indices[0].query_id
    assert indices[0].strand == "pos"

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
    assert "rna_R1_SRR18677638.fastq.gz" == index.query_id
    assert index.strand == "pos"
    regions = index.rcv
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

from seqspec.seqspec_index import Coordinate
def test_seqspec_index_without_ids(dogmaseq_dig_spec: Assay):
    """Test seqspec_index without providing ids (uses get_index_by_files)"""
    # Test file indexing without specific IDs
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="rna", ids=[], idtype="file"
    )
    
    # Should return indices for all files in the modality
    assert len(indices) > 0
    
    # Check structure of returned indices
    for coord in indices:
        assert isinstance(coord, Coordinate)
        assert coord.query_type == "File"
        assert isinstance(coord.rcv, list)
        assert len(coord.rcv) > 0
        assert all(isinstance(region, RegionCoordinate) for region in coord.rcv)


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
    assert "rna_R1" in rna_r1_index.query_id
    assert rna_r1_index.strand == "pos"
    rna_r1_regions = rna_r1_index.rcv
    assert len(rna_r1_regions) == 2  # cell_bc + umi
    
    # Check second read (rna_R2) - this has negative strand
    rna_r2_index = indices[1]
    assert "rna_R2" in rna_r2_index.query_id
    assert rna_r2_index.strand == "neg"  # Fixed: rna_R2 has negative strand
    rna_r2_regions = rna_r2_index.rcv
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
    
    # Validate returned file IDs and structure
    file_ids = {"rna_R1_SRR18677638.fastq.gz", "rna_R2_SRR18677638.fastq.gz"}
    returned_ids = {coord.query_id for coord in indices}
    assert returned_ids == file_ids

    for coord in indices:
        assert isinstance(coord, Coordinate)
        assert coord.strand in ["pos", "neg"]
        assert isinstance(coord.rcv, list)
        assert all(isinstance(region, RegionCoordinate) for region in coord.rcv)
        if "rna_R1" in coord.query_id:
            assert len(coord.rcv) == 2
        if "rna_R2" in coord.query_id:
            assert len(coord.rcv) == 1


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
    for coord in indices:
        assert isinstance(coord, Coordinate)
        assert coord.strand in ["pos", "neg"]
        assert isinstance(coord.rcv, list)
        assert len(coord.rcv) > 0
        assert all(isinstance(region, RegionCoordinate) for region in coord.rcv)


def test_seqspec_index_different_modalities(dogmaseq_dig_spec: Assay):
    """Test seqspec_index across different modalities"""
    # Test RNA modality
    rna_indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="rna", ids=["rna_R1"], idtype="read"
    )
    assert len(rna_indices) == 1
    assert "rna_R1" == rna_indices[0].query_id
    
    # Test ATAC modality
    atac_indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="atac", ids=["atac_R1"], idtype="read"
    )
    assert len(atac_indices) == 1
    assert "atac_R1" == atac_indices[0].query_id
    
    # Test protein modality
    protein_indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="protein", ids=["protein_R1"], idtype="read"
    )
    assert len(protein_indices) == 1
    assert "protein_R1" == protein_indices[0].query_id
    
    # Test tag modality
    tag_indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="tag", ids=["tag_R1"], idtype="read"
    )
    assert len(tag_indices) == 1
    assert "tag_R1" == tag_indices[0].query_id


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
    assert "rna_R1"  == indices[0].query_id
    assert indices[0].strand == "pos"  # Strand should still be pos for this read
    
    # Check that regions are still RegionCoordinate objects
    regions = indices[0].rcv
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
        
        for coord in indices:
            assert isinstance(coord, Coordinate)
            assert hasattr(coord, "strand")
            assert coord.strand in ["pos", "neg"]
            assert isinstance(coord.rcv, list)
            assert len(coord.rcv) > 0
            assert all(isinstance(region, RegionCoordinate) for region in coord.rcv)


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

    # Additional pragmatic coverage: kb-single, seqkit, relative, splitcode formats
    # kb-single chooses the longest feature among feature regions
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="rna", ids=["rna_R1", "rna_R2"], idtype="read"
    )
    formatted_kb_single = format_index(indices, "kb-single")
    assert formatted_kb_single.endswith(":1,0,102")

    # seqkit subseq for a specific subregion_type
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="rna", ids=["rna_R1"], idtype="read"
    )
    seqkit_subseq = format_index(indices, "seqkit", subregion_type="barcode")
    assert seqkit_subseq.strip() == "1:16"

    # relative output should be non-empty and tab-delimited when a linker exists
    # Use the ATAC region which contains a linker
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="atac", ids=["atac"], idtype="region"
    )
    rel = format_index(indices, "relative")
    assert isinstance(rel, str) and ("\t" in rel) and len(rel) > 0

    # splitcode should contain @extract lines and groups header
    split = format_index(indices, "splitcode")
    assert "@extract" in split
    assert "groups\tids\ttags\tdistances\tlocations" in split

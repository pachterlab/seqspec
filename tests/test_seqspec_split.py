from seqspec.seqspec_split import seqspec_split
from seqspec.Assay import Assay


def test_seqspec_split(dogmaseq_dig_spec: Assay):
    """Test seqspec_split function with dogmaseq-dig spec"""
    # Split the spec into individual modality specs
    split_specs = seqspec_split(dogmaseq_dig_spec)
    
    # Check that we get the expected number of specs
    expected_modalities = ["protein", "tag", "rna", "atac"]
    assert len(split_specs) == len(expected_modalities)
    
    # Check each split spec
    for spec in split_specs:
        # Each spec should have exactly one modality
        modalities = spec.list_modalities()
        assert len(modalities) == 1
        modality = modalities[0]
        assert modality in expected_modalities
        
        # Check that the spec has the correct metadata
        assert spec.assay_id == dogmaseq_dig_spec.assay_id
        assert spec.name == dogmaseq_dig_spec.name
        assert spec.doi == dogmaseq_dig_spec.doi
        assert spec.date == dogmaseq_dig_spec.date
        assert spec.description == dogmaseq_dig_spec.description
        assert spec.seqspec_version == dogmaseq_dig_spec.seqspec_version
        
        # Check that sequence_spec contains only reads for this modality
        for read in spec.sequence_spec:
            assert read.modality == modality
            
        # Check that library_spec contains only regions for this modality
        assert len(spec.library_spec) == 1
        lib_spec = spec.library_spec[0]
        # The library spec should be the same as the original for this modality
        original_lib_spec = dogmaseq_dig_spec.get_libspec(modality)
        assert lib_spec.region_id == original_lib_spec.region_id
        assert lib_spec.sequence == original_lib_spec.sequence


def test_seqspec_split_protein_modality(dogmaseq_dig_spec: Assay):
    """Test specific protein modality split"""
    split_specs = seqspec_split(dogmaseq_dig_spec)
    
    # Find the protein spec
    protein_spec = None
    for spec in split_specs:
        if "protein" in spec.list_modalities():
            protein_spec = spec
            break
    
    assert protein_spec is not None
    assert protein_spec.list_modalities() == ["protein"]
    
    # Check protein-specific reads
    protein_reads = protein_spec.sequence_spec
    read_ids = [read.read_id for read in protein_reads]
    expected_protein_reads = ["protein_R1", "protein_R2"]
    assert set(read_ids) == set(expected_protein_reads)
    
    # Check protein-specific library spec
    protein_lib_spec = protein_spec.library_spec[0]
    assert protein_lib_spec.region_id == "protein"


def test_seqspec_split_rna_modality(dogmaseq_dig_spec: Assay):
    """Test specific RNA modality split"""
    split_specs = seqspec_split(dogmaseq_dig_spec)
    
    # Find the RNA spec
    rna_spec = None
    for spec in split_specs:
        if "rna" in spec.list_modalities():
            rna_spec = spec
            break
    
    assert rna_spec is not None
    assert rna_spec.list_modalities() == ["rna"]
    
    # Check RNA-specific reads
    rna_reads = rna_spec.sequence_spec
    read_ids = [read.read_id for read in rna_reads]
    expected_rna_reads = ["rna_R1", "rna_R2"]
    assert set(read_ids) == set(expected_rna_reads)
    
    # Check RNA-specific library spec
    rna_lib_spec = rna_spec.library_spec[0]
    assert rna_lib_spec.region_id == "rna"


def test_seqspec_split_atac_modality(dogmaseq_dig_spec: Assay):
    """Test specific ATAC modality split"""
    split_specs = seqspec_split(dogmaseq_dig_spec)
    
    # Find the ATAC spec
    atac_spec = None
    for spec in split_specs:
        if "atac" in spec.list_modalities():
            atac_spec = spec
            break
    
    assert atac_spec is not None
    assert atac_spec.list_modalities() == ["atac"]
    
    # Check ATAC-specific reads
    atac_reads = atac_spec.sequence_spec
    read_ids = [read.read_id for read in atac_reads]
    expected_atac_reads = ["atac_R1", "atac_R2", "atac_R3"]
    assert set(read_ids) == set(expected_atac_reads)
    
    # Check ATAC-specific library spec
    atac_lib_spec = atac_spec.library_spec[0]
    assert atac_lib_spec.region_id == "atac"


def test_seqspec_split_tag_modality(dogmaseq_dig_spec: Assay):
    """Test specific tag modality split"""
    split_specs = seqspec_split(dogmaseq_dig_spec)
    
    # Find the tag spec
    tag_spec = None
    for spec in split_specs:
        if "tag" in spec.list_modalities():
            tag_spec = spec
            break
    
    assert tag_spec is not None
    assert tag_spec.list_modalities() == ["tag"]
    
    # Check tag-specific reads
    tag_reads = tag_spec.sequence_spec
    read_ids = [read.read_id for read in tag_reads]
    expected_tag_reads = ["tag_R1", "tag_R2"]
    assert set(read_ids) == set(expected_tag_reads)
    
    # Check tag-specific library spec
    tag_lib_spec = tag_spec.library_spec[0]
    assert tag_lib_spec.region_id == "tag" 
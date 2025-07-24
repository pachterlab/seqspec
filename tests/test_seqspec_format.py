"""Tests for seqspec_format module."""


from seqspec.Assay import Assay
from seqspec.Region import Region

from seqspec.seqspec_format import format_spec


def test_format_spec_basic():
    """Test basic format_spec functionality with an unformatted spec"""
    # Create an unformatted spec with regions that need formatting
    child_region = Region(
        region_id="child",
        region_type="barcode",
        name="Child",
        sequence_type="fixed",
        sequence="ATCG",
        min_len=4,  # Set to actual length
        max_len=4,  # Set to actual length
        regions=[]
    )
    
    parent_region = Region(
        region_id="parent",
        region_type="cdna",
        name="Parent",
        sequence_type="joined",
        sequence="",  # Will be updated
        min_len=0,    # Will be updated
        max_len=0,    # Will be updated
        regions=[child_region]
    )
    
    spec = Assay(
        seqspec_version="0.3.0",
        assay_id="test",
        name="Test",
        doi="",
        date="20240101",
        description="",
        modalities=["rna"],
        lib_struct="",
        sequence_protocol="",
        sequence_kit="",
        library_protocol="",
        library_kit="",
        sequence_spec=[],
        library_spec=[parent_region]
    )
    
    # Store original values
    original_parent_sequence = parent_region.sequence
    original_parent_lengths = (parent_region.min_len, parent_region.max_len)
    
    # Call format_spec
    format_spec(spec)
    
    # Verify that parent region was updated
    assert parent_region.sequence != original_parent_sequence
    assert (parent_region.min_len, parent_region.max_len) != original_parent_lengths
    
    # Verify specific updates
    assert parent_region.sequence == "ATCG"
    assert parent_region.min_len == 4
    assert parent_region.max_len == 4
    # Child region should remain unchanged since it was already properly set
    assert child_region.min_len == 4
    assert child_region.max_len == 4


def test_format_spec_random_sequences():
    """Test that random sequences are properly formatted"""
    # Create a simple spec with random sequences
    random_region = Region(
        region_id="test_random",
        region_type="barcode",
        name="Test Random",
        sequence_type="random",
        sequence="",
        min_len=10,
        max_len=10,
        regions=[]
    )
    
    spec = Assay(
        seqspec_version="0.3.0",
        assay_id="test",
        name="Test",
        doi="",
        date="20240101",
        description="",
        modalities=["rna"],
        lib_struct="",
        sequence_protocol="",
        sequence_kit="",
        library_protocol="",
        library_kit="",
        sequence_spec=[],
        library_spec=[random_region]
    )
    
    # Call format_spec
    format_spec(spec)
    
    # Verify random sequence was set to "X" * min_len
    assert random_region.sequence == "X" * 10


def test_format_spec_onlist_sequences():
    """Test that onlist sequences are properly formatted"""
    # Create a simple spec with onlist sequences
    onlist_region = Region(
        region_id="test_onlist",
        region_type="barcode",
        name="Test Onlist",
        sequence_type="onlist",
        sequence="",
        min_len=8,
        max_len=8,
        regions=[]
    )
    
    spec = Assay(
        seqspec_version="0.3.0",
        assay_id="test",
        name="Test",
        doi="",
        date="20240101",
        description="",
        modalities=["rna"],
        lib_struct="",
        sequence_protocol="",
        sequence_kit="",
        library_protocol="",
        library_kit="",
        sequence_spec=[],
        library_spec=[onlist_region]
    )
    
    # Call format_spec
    format_spec(spec)
    
    # Verify onlist sequence was set to "N" * min_len
    assert onlist_region.sequence == "N" * 8


def test_format_spec_nested_regions():
    """Test that nested regions are properly formatted"""
    # Create nested regions
    child_region = Region(
        region_id="child",
        region_type="barcode",
        name="Child",
        sequence_type="fixed",
        sequence="ATCG",
        min_len=4,
        max_len=4,
        regions=[]
    )
    
    parent_region = Region(
        region_id="parent",
        region_type="cdna",
        name="Parent",
        sequence_type="joined",
        sequence="",
        min_len=0,
        max_len=0,
        regions=[child_region]
    )
    
    spec = Assay(
        seqspec_version="0.3.0",
        assay_id="test",
        name="Test",
        doi="",
        date="20240101",
        description="",
        modalities=["rna"],
        lib_struct="",
        sequence_protocol="",
        sequence_kit="",
        library_protocol="",
        library_kit="",
        sequence_spec=[],
        library_spec=[parent_region]
    )
    
    # Call format_spec
    format_spec(spec)
    
    # Verify both parent and child were updated
    assert parent_region.sequence == "ATCG"  # Should be joined from child
    assert parent_region.min_len == 4
    assert parent_region.max_len == 4
    assert child_region.sequence == "ATCG"


def test_format_spec_preserves_fixed_sequences():
    """Test that fixed sequences are preserved"""
    fixed_region = Region(
        region_id="test_fixed",
        region_type="barcode",
        name="Test Fixed",
        sequence_type="fixed",
        sequence="GATCGATC",
        min_len=8,
        max_len=8,
        regions=[]
    )
    
    spec = Assay(
        seqspec_version="0.3.0",
        assay_id="test",
        name="Test",
        doi="",
        date="20240101",
        description="",
        modalities=["rna"],
        lib_struct="",
        sequence_protocol="",
        sequence_kit="",
        library_protocol="",
        library_kit="",
        sequence_spec=[],
        library_spec=[fixed_region]
    )
    
    original_sequence = fixed_region.sequence
    
    # Call format_spec
    format_spec(spec)
    
    # Verify fixed sequence was preserved
    assert fixed_region.sequence == original_sequence


def test_format_spec_with_dogmaseq_spec(dogmaseq_dig_spec: Assay):
    """Test format_spec with the dogmaseq-dig spec"""
    # Create a copy to avoid modifying the original
    spec = dogmaseq_dig_spec.model_copy(deep=True)
    
    # Call format_spec
    format_spec(spec)
    
    # Verify that regions have been processed
    # Note: Some regions (like "named" regions) may remain empty
    for lib_spec in spec.library_spec:
        for region in lib_spec.get_leaves():
            # Check that lengths are reasonable
            assert region.min_len >= 0
            assert region.max_len >= region.min_len
            # For non-named regions, sequences should be populated
            if region.region_type != "named":
                assert region.sequence != "", f"Region {region.region_id} has empty sequence"





# def test_run_format_file_output(dogmaseq_dig_spec: Assay, tmp_path):
#     """Test run_format with file output"""
#     # Create a temporary spec file
#     spec_file = tmp_path / "test_spec.yaml"
#     output_file = tmp_path / "output_spec.yaml"
#     dogmaseq_dig_spec.to_YAML(spec_file)
    
#     # Mock the parser and args
#     class MockParser(ArgumentParser):
#         def error(self, msg):
#             raise ValueError(msg)
    
#     class MockArgs(Namespace):
#         def __init__(self, yaml_path, output=None):
#             super().__init__()
#             self.yaml = yaml_path
#             self.output = output
    
#     parser = MockParser()
#     args = MockArgs(spec_file, output_file)
    
#     # Run format
#     run_format(parser, args)
    
#     # Verify output file was created
#     assert output_file.exists()
    
#     # Verify the output file can be loaded
#     output_spec = load_spec(output_file)
#     assert isinstance(output_spec, Assay)
#     assert output_spec.assay_id == dogmaseq_dig_spec.assay_id





def test_format_spec_complex_structure():
    """Test format_spec with a complex nested structure"""
    # Create a complex nested structure
    leaf1 = Region(
        region_id="leaf1",
        region_type="barcode",
        name="Leaf 1",
        sequence_type="fixed",
        sequence="ATCG",
        min_len=4,
        max_len=4,
        regions=[]
    )
    
    leaf2 = Region(
        region_id="leaf2",
        region_type="umi",
        name="Leaf 2",
        sequence_type="random",
        sequence="",
        min_len=6,
        max_len=6,
        regions=[]
    )
    
    middle = Region(
        region_id="middle",
        region_type="linker",
        name="Middle",
        sequence_type="joined",
        sequence="",
        min_len=0,
        max_len=0,
        regions=[leaf1, leaf2]
    )
    
    root = Region(
        region_id="root",
        region_type="cdna",
        name="Root",
        sequence_type="joined",
        sequence="",
        min_len=0,
        max_len=0,
        regions=[middle]
    )
    
    spec = Assay(
        seqspec_version="0.3.0",
        assay_id="test",
        name="Test",
        doi="",
        date="20240101",
        description="",
        modalities=["rna"],
        lib_struct="",
        sequence_protocol="",
        sequence_kit="",
        library_protocol="",
        library_kit="",
        sequence_spec=[],
        library_spec=[root]
    )
    
    # Call format_spec
    format_spec(spec)
    
    # Verify all levels were updated
    assert root.sequence == "ATCG" + "X" * 6  # fixed + random
    assert root.min_len == 10
    assert root.max_len == 10
    
    assert middle.sequence == "ATCG" + "X" * 6
    assert middle.min_len == 10
    assert middle.max_len == 10
    
    assert leaf1.sequence == "ATCG"
    assert leaf1.min_len == 4
    assert leaf1.max_len == 4
    
    assert leaf2.sequence == "X" * 6
    assert leaf2.min_len == 6
    assert leaf2.max_len == 6 
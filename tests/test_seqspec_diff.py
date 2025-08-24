"""Tests for seqspec_diff module."""

from argparse import ArgumentParser, Namespace
from pathlib import Path

import pytest

from seqspec.Assay import Assay
from seqspec.Region import Region
from seqspec.seqspec_diff import compare_specs, compare_regions, diff_regions, run_diff


def test_diff_regions_identical():
    """Test diff_regions with identical regions"""
    region_a = Region(
        region_id="test_region",
        region_type="barcode",
        name="Test Region",
        sequence_type="fixed",
        sequence="ATCG",
        min_len=4,
        max_len=4,
        regions=[]
    )
    
    region_b = Region(
        region_id="test_region",
        region_type="barcode",
        name="Test Region",
        sequence_type="fixed",
        sequence="ATCG",
        min_len=4,
        max_len=4,
        regions=[]
    )
    
    differences = diff_regions(region_a, region_b)
    assert differences == []


def test_diff_regions_different_properties():
    """Test diff_regions with different region properties"""
    region_a = Region(
        region_id="test_region",
        region_type="barcode",
        name="Test Region A",
        sequence_type="fixed",
        sequence="ATCG",
        min_len=4,
        max_len=4,
        regions=[]
    )
    
    region_b = Region(
        region_id="test_region",
        region_type="umi",
        name="Test Region B",
        sequence_type="random",
        sequence="XXXX",
        min_len=6,
        max_len=6,
        regions=[]
    )
    
    differences = diff_regions(region_a, region_b)
    
    expected_diffs = [
        "region_type: barcode != umi",
        "name: Test Region A != Test Region B",
        "sequence_type: fixed != random",
        "sequence: ATCG != XXXX",
        "min_len: 4 != 6",
        "max_len: 4 != 6"
    ]
    
    assert len(differences) == len(expected_diffs)
    for diff in expected_diffs:
        assert diff in differences


def test_diff_regions_partial_differences():
    """Test diff_regions with only some properties different"""
    region_a = Region(
        region_id="test_region",
        region_type="barcode",
        name="Test Region",
        sequence_type="fixed",
        sequence="ATCG",
        min_len=4,
        max_len=4,
        regions=[]
    )
    
    region_b = Region(
        region_id="test_region",
        region_type="barcode",
        name="Test Region",
        sequence_type="fixed",
        sequence="GCTA",  # Different sequence
        min_len=4,
        max_len=5,  # Different max_len
        regions=[]
    )
    
    differences = diff_regions(region_a, region_b)
    
    expected_diffs = [
        "sequence: ATCG != GCTA",
        "max_len: 4 != 5"
    ]
    
    assert len(differences) == len(expected_diffs)
    for diff in expected_diffs:
        assert diff in differences


def test_compare_regions_identical():
    """Test compare_regions with identical region lists"""
    regions_a = [
        Region(
            region_id="region1",
            region_type="barcode",
            name="Region 1",
            sequence_type="fixed",
            sequence="ATCG",
            min_len=4,
            max_len=4,
            regions=[]
        ),
        Region(
            region_id="region2",
            region_type="umi",
            name="Region 2",
            sequence_type="random",
            sequence="XXXX",
            min_len=6,
            max_len=6,
            regions=[]
        )
    ]
    
    regions_b = [
        Region(
            region_id="region1",
            region_type="barcode",
            name="Region 1",
            sequence_type="fixed",
            sequence="ATCG",
            min_len=4,
            max_len=4,
            regions=[]
        ),
        Region(
            region_id="region2",
            region_type="umi",
            name="Region 2",
            sequence_type="random",
            sequence="XXXX",
            min_len=6,
            max_len=6,
            regions=[]
        )
    ]
    
    differences = compare_regions(regions_a, regions_b)
    assert differences == []


def test_compare_regions_unique_regions():
    """Test compare_regions with regions unique to each list"""
    regions_a = [
        Region(
            region_id="region1",
            region_type="barcode",
            name="Region 1",
            sequence_type="fixed",
            sequence="ATCG",
            min_len=4,
            max_len=4,
            regions=[]
        ),
        Region(
            region_id="region2",
            region_type="umi",
            name="Region 2",
            sequence_type="random",
            sequence="XXXX",
            min_len=6,
            max_len=6,
            regions=[]
        )
    ]
    
    regions_b = [
        Region(
            region_id="region1",
            region_type="barcode",
            name="Region 1",
            sequence_type="fixed",
            sequence="ATCG",
            min_len=4,
            max_len=4,
            regions=[]
        ),
        Region(
            region_id="region3",
            region_type="cdna",
            name="Region 3",
            sequence_type="joined",
            sequence="NNNN",
            min_len=8,
            max_len=8,
            regions=[]
        )
    ]
    
    differences = compare_regions(regions_a, regions_b)
    
    # Should have differences for unique regions
    assert len(differences) > 0
    assert "  Regions only in spec A:" in differences
    assert "  Regions only in spec B:" in differences
    assert "    - region2" in differences
    assert "    - region3" in differences


def test_compare_regions_different_properties():
    """Test compare_regions with regions that have different properties"""
    regions_a = [
        Region(
            region_id="region1",
            region_type="barcode",
            name="Region 1",
            sequence_type="fixed",
            sequence="ATCG",
            min_len=4,
            max_len=4,
            regions=[]
        )
    ]
    
    regions_b = [
        Region(
            region_id="region1",
            region_type="barcode",
            name="Region 1",
            sequence_type="fixed",
            sequence="GCTA",  # Different sequence
            min_len=4,
            max_len=4,
            regions=[]
        )
    ]
    
    differences = compare_regions(regions_a, regions_b)
    
    # Should have differences for the common region
    assert len(differences) > 0
    assert "  Region 'region1' differences:" in differences
    assert "    - sequence: ATCG != GCTA" in differences


def test_compare_regions_empty_lists():
    """Test compare_regions with empty region lists"""
    differences = compare_regions([], [])
    assert differences == []


def test_compare_regions_one_empty():
    """Test compare_regions with one empty list"""
    regions_a = [
        Region(
            region_id="region1",
            region_type="barcode",
            name="Region 1",
            sequence_type="fixed",
            sequence="ATCG",
            min_len=4,
            max_len=4,
            regions=[]
        )
    ]
    
    differences = compare_regions(regions_a, [])
    
    assert len(differences) > 0
    assert "  Regions only in spec A:" in differences
    assert "    - region1" in differences


def test_compare_specs_identical():
    """Test compare_specs with identical specs"""
    spec_a = Assay(
        seqspec_version="0.3.0",
        assay_id="test",
        name="Test Assay",
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
        library_spec=[
            Region(
                region_id="rna",
                region_type="rna",
                name="rna",
                sequence_type="joined",
                sequence="",
                min_len=0,
                max_len=0,
                regions=[
                    Region(
                        region_id="region1",
                        region_type="barcode",
                        name="Region 1",
                        sequence_type="fixed",
                        sequence="ATCG",
                        min_len=4,
                        max_len=4,
                        regions=[]
                    )
                ]
            )
        ]
    )
    
    spec_b = Assay(
        seqspec_version="0.3.0",
        assay_id="test",
        name="Test Assay",
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
        library_spec=[
            Region(
                region_id="rna",
                region_type="rna",
                name="rna",
                sequence_type="joined",
                sequence="",
                min_len=0,
                max_len=0,
                regions=[
                    Region(
                        region_id="region1",
                        region_type="barcode",
                        name="Region 1",
                        sequence_type="fixed",
                        sequence="ATCG",
                        min_len=4,
                        max_len=4,
                        regions=[]
                    )
                ]
            )
        ]
    )
    
    differences = compare_specs(spec_a, spec_b)
    assert differences == "No differences found"


def test_compare_specs_different_modalities():
    """Test compare_specs with different modalities"""
    spec_a = Assay(
        seqspec_version="0.3.0",
        assay_id="test",
        name="Test Assay",
        doi="",
        date="20240101",
        description="",
        modalities=["rna", "protein"],
        lib_struct="",
        sequence_protocol="",
        sequence_kit="",
        library_protocol="",
        library_kit="",
        sequence_spec=[],
        library_spec=[
            Region(
                region_id="rna",
                region_type="rna",
                name="rna",
                sequence_type="joined",
                sequence="",
                min_len=0,
                max_len=0,
                regions=[
                    Region(
                        region_id="rna_region",
                        region_type="barcode",
                        name="RNA Region",
                        sequence_type="fixed",
                        sequence="ATCG",
                        min_len=4,
                        max_len=4,
                        regions=[]
                    )
                ]
            ),
            Region(
                region_id="protein",
                region_type="protein",
                name="protein",
                sequence_type="joined",
                sequence="",
                min_len=0,
                max_len=0,
                regions=[
                    Region(
                        region_id="protein_region",
                        region_type="umi",
                        name="Protein Region",
                        sequence_type="random",
                        sequence="XXXX",
                        min_len=6,
                        max_len=6,
                        regions=[]
                    )
                ]
            )
        ]
    )
    
    spec_b = Assay(
        seqspec_version="0.3.0",
        assay_id="test",
        name="Test Assay",
        doi="",
        date="20240101",
        description="",
        modalities=["rna", "atac"],
        lib_struct="",
        sequence_protocol="",
        sequence_kit="",
        library_protocol="",
        library_kit="",
        sequence_spec=[],
        library_spec=[
            Region(
                region_id="rna",
                region_type="rna",
                name="rna",
                sequence_type="joined",
                sequence="",
                min_len=0,
                max_len=0,
                regions=[
                    Region(
                        region_id="rna_region",
                        region_type="barcode",
                        name="RNA Region",
                        sequence_type="fixed",
                        sequence="ATCG",
                        min_len=4,
                        max_len=4,
                        regions=[]
                    )
                ]
            ),
            Region(
                region_id="atac",
                region_type="atac",
                name="atac",
                sequence_type="joined",
                sequence="",
                min_len=0,
                max_len=0,
                regions=[
                    Region(
                        region_id="atac_region",
                        region_type="cdna",
                        name="ATAC Region",
                        sequence_type="joined",
                        sequence="NNNN",
                        min_len=8,
                        max_len=8,
                        regions=[]
                    )
                ]
            )
        ]
    )
    
    differences = compare_specs(spec_a, spec_b)
    
    assert "Modalities differ:" in differences
    assert "Spec A: protein, rna" in differences
    assert "Spec B: atac, rna" in differences


def test_compare_specs_common_modality_differences():
    """Test compare_specs with common modality but different regions"""
    spec_a = Assay(
        seqspec_version="0.3.0",
        assay_id="test",
        name="Test Assay",
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
        library_spec=[
            Region(
                region_id="rna",
                region_type="rna",
                name="rna",
                sequence_type="joined",
                sequence="",
                min_len=0,
                max_len=0,
                regions=[
                    Region(
                        region_id="region1",
                        region_type="barcode",
                        name="Region 1",
                        sequence_type="fixed",
                        sequence="ATCG",
                        min_len=4,
                        max_len=4,
                        regions=[]
                    )
                ]
            )
        ]
    )
    
    spec_b = Assay(
        seqspec_version="0.3.0",
        assay_id="test",
        name="Test Assay",
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
        library_spec=[
            Region(
                region_id="rna",
                region_type="rna",
                name="rna",
                sequence_type="joined",
                sequence="",
                min_len=0,
                max_len=0,
                regions=[
                    Region(
                        region_id="region1",
                        region_type="barcode",
                        name="Region 1",
                        sequence_type="fixed",
                        sequence="GCTA",  # Different sequence
                        min_len=4,
                        max_len=4,
                        regions=[]
                    )
                ]
            )
        ]
    )
    
    differences = compare_specs(spec_a, spec_b)
    
    assert "Modality 'rna' differences:" in differences
    assert "Region 'region1' differences:" in differences
    assert "sequence: ATCG != GCTA" in differences


def test_compare_specs_multiple_modalities():
    """Test compare_specs with multiple modalities"""
    spec_a = Assay(
        seqspec_version="0.3.0",
        assay_id="test",
        name="Test Assay",
        doi="",
        date="20240101",
        description="",
        modalities=["rna", "protein"],
        lib_struct="",
        sequence_protocol="",
        sequence_kit="",
        library_protocol="",
        library_kit="",
        sequence_spec=[],
        library_spec=[
            Region(
                region_id="rna",
                region_type="rna",
                name="rna",
                sequence_type="joined",
                sequence="",
                min_len=0,
                max_len=0,
                regions=[
                    Region(
                        region_id="rna_region",
                        region_type="barcode",
                        name="RNA Region",
                        sequence_type="fixed",
                        sequence="ATCG",
                        min_len=4,
                        max_len=4,
                        regions=[]
                    )
                ]
            ),
            Region(
                region_id="protein",
                region_type="protein",
                name="protein",
                sequence_type="joined",
                sequence="",
                min_len=0,
                max_len=0,
                regions=[
                    Region(
                        region_id="protein_region",
                        region_type="umi",
                        name="Protein Region",
                        sequence_type="random",
                        sequence="XXXX",
                        min_len=6,
                        max_len=6,
                        regions=[]
                    )
                ]
            )
        ]
    )
    
    spec_b = Assay(
        seqspec_version="0.3.0",
        assay_id="test",
        name="Test Assay",
        doi="",
        date="20240101",
        description="",
        modalities=["rna", "protein"],
        lib_struct="",
        sequence_protocol="",
        sequence_kit="",
        library_protocol="",
        library_kit="",
        sequence_spec=[],
        library_spec=[
            Region(
                region_id="rna",
                region_type="rna",
                name="rna",
                sequence_type="joined",
                sequence="",
                min_len=0,
                max_len=0,
                regions=[
                    Region(
                        region_id="rna_region",
                        region_type="barcode",
                        name="RNA Region",
                        sequence_type="fixed",
                        sequence="GCTA",  # Different sequence
                        min_len=4,
                        max_len=4,
                        regions=[]
                    )
                ]
            ),
            Region(
                region_id="protein",
                region_type="protein",
                name="protein",
                sequence_type="joined",
                sequence="",
                min_len=0,
                max_len=0,
                regions=[
                    Region(
                        region_id="protein_region",
                        region_type="umi",
                        name="Protein Region",
                        sequence_type="random",
                        sequence="XXXX",
                        min_len=6,
                        max_len=6,
                        regions=[]
                    )
                ]
            )
        ]
    )
    
    differences = compare_specs(spec_a, spec_b)
    
    # Should only show differences for the rna modality
    assert "Modality 'rna' differences:" in differences
    assert "sequence: ATCG != GCTA" in differences
    # Should not show differences for protein modality
    assert "Modality 'protein' differences:" not in differences


def test_compare_specs_with_dogmaseq_spec():
    """Test compare_specs with the dogmaseq-dig spec"""
    from seqspec.utils import load_spec
    
    spec = load_spec("tests/fixtures/spec.yaml")
    
    # Create a modified version of the spec
    modified_spec = spec.model_copy(deep=True)
    
    # Modify a region in the RNA modality
    rna_libspec = modified_spec.get_libspec("rna")
    for region in rna_libspec.get_leaves():
        if region.region_id == "rna_cell_bc":
            region.sequence = "MODIFIED_SEQUENCE"
            break
    
    differences = compare_specs(spec, modified_spec)
    
    assert "Modality 'rna' differences:" in differences
    assert "Region 'rna_cell_bc' differences:" in differences
    assert "sequence:" in differences


def test_run_diff_stdout(tmp_path):
    """Test run_diff with stdout output"""
    # Create two different spec files
    spec_a = Assay(
        seqspec_version="0.3.0",
        assay_id="test_a",
        name="Test Assay A",
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
        library_spec=[
            Region(
                region_id="rna",
                region_type="rna",
                name="rna",
                sequence_type="joined",
                sequence="",
                min_len=0,
                max_len=0,
                regions=[
                    Region(
                        region_id="region1",
                        region_type="barcode",
                        name="Region 1",
                        sequence_type="fixed",
                        sequence="ATCG",
                        min_len=4,
                        max_len=4,
                        regions=[]
                    )
                ]
            )
        ]
    )
    
    spec_b = Assay(
        seqspec_version="0.3.0",
        assay_id="test_b",
        name="Test Assay B",
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
        library_spec=[
            Region(
                region_id="rna",
                region_type="rna",
                name="rna",
                sequence_type="joined",
                sequence="",
                min_len=0,
                max_len=0,
                regions=[
                    Region(
                        region_id="region1",
                        region_type="barcode",
                        name="Region 1",
                        sequence_type="fixed",
                        sequence="GCTA",  # Different sequence
                        min_len=4,
                        max_len=4,
                        regions=[]
                    )
                ]
            )
        ]
    )
    
    # Create temporary spec files
    spec_file_a = tmp_path / "spec_a.yaml"
    spec_file_b = tmp_path / "spec_b.yaml"
    spec_a.to_YAML(spec_file_a)
    spec_b.to_YAML(spec_file_b)
    
    # Mock the parser and args
    class MockParser(ArgumentParser):
        def error(self, msg):
            raise ValueError(msg)
    
    class MockArgs(Namespace):
        def __init__(self, yaml_a, yaml_b, output=None):
            super().__init__()
            self.yamlA = yaml_a
            self.yamlB = yaml_b
            self.output = output
    
    parser = MockParser()
    args = MockArgs(spec_file_a, spec_file_b)
    
    # Test that run_diff doesn't raise an exception
    # We can't easily capture stdout in this test, so we just verify it runs
    run_diff(parser, args)


def test_run_diff_file_output(tmp_path):
    """Test run_diff with file output"""
    # Create two different spec files
    spec_a = Assay(
        seqspec_version="0.3.0",
        assay_id="test_a",
        name="Test Assay A",
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
        library_spec=[
            Region(
                region_id="rna",
                region_type="rna",
                name="rna",
                sequence_type="joined",
                sequence="",
                min_len=0,
                max_len=0,
                regions=[
                    Region(
                        region_id="region1",
                        region_type="barcode",
                        name="Region 1",
                        sequence_type="fixed",
                        sequence="ATCG",
                        min_len=4,
                        max_len=4,
                        regions=[]
                    )
                ]
            )
        ]
    )
    
    spec_b = Assay(
        seqspec_version="0.3.0",
        assay_id="test_b",
        name="Test Assay B",
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
        library_spec=[
            Region(
                region_id="rna",
                region_type="rna",
                name="rna",
                sequence_type="joined",
                sequence="",
                min_len=0,
                max_len=0,
                regions=[
                    Region(
                        region_id="region1",
                        region_type="barcode",
                        name="Region 1",
                        sequence_type="fixed",
                        sequence="GCTA",  # Different sequence
                        min_len=4,
                        max_len=4,
                        regions=[]
                    )
                ]
            )
        ]
    )
    
    # Create temporary spec files
    spec_file_a = tmp_path / "spec_a.yaml"
    spec_file_b = tmp_path / "spec_b.yaml"
    output_file = tmp_path / "diff.txt"
    spec_a.to_YAML(spec_file_a)
    spec_b.to_YAML(spec_file_b)
    
    # Mock the parser and args
    class MockParser(ArgumentParser):
        def error(self, msg):
            raise ValueError(msg)
    
    class MockArgs(Namespace):
        def __init__(self, yaml_a, yaml_b, output=None):
            super().__init__()
            self.yamlA = yaml_a
            self.yamlB = yaml_b
            self.output = output
    
    parser = MockParser()
    args = MockArgs(spec_file_a, spec_file_b, output_file)
    
    # Run diff
    run_diff(parser, args)
    
    # Verify output file was created
    assert output_file.exists()
    
    # Verify the output file contains expected content
    content = output_file.read_text()
    assert "Modality 'rna' differences:" in content
    assert "Region 'region1' differences:" in content
    assert "sequence: ATCG != GCTA" in content


def test_run_diff_nonexistent_file(tmp_path):
    """Test run_diff with nonexistent input file"""
    # Create one spec file
    spec_a = Assay(
        seqspec_version="0.3.0",
        assay_id="test_a",
        name="Test Assay A",
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
        library_spec=[]
    )
    
    spec_file_a = tmp_path / "spec_a.yaml"
    spec_a.to_YAML(spec_file_a)
    
    # Mock the parser and args
    class MockParser(ArgumentParser):
        def error(self, msg):
            raise ValueError(msg)
    
    class MockArgs(Namespace):
        def __init__(self, yaml_a, yaml_b, output=None):
            super().__init__()
            self.yamlA = yaml_a
            self.yamlB = yaml_b
            self.output = output
    
    parser = MockParser()
    args = MockArgs(spec_file_a, tmp_path / "nonexistent.yaml")
    
    # Test that it raises an error for nonexistent file
    with pytest.raises(ValueError, match="Input file B does not exist"):
        run_diff(parser, args) 
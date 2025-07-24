from seqspec.seqspec_version import seqspec_version, format_version
from seqspec.Assay import Assay


def test_seqspec_version(dogmaseq_dig_spec: Assay):
    """Test seqspec_version function with dogmaseq-dig spec"""
    # Get version information
    vinfo = seqspec_version(dogmaseq_dig_spec)
    
    # Check that we get the expected structure
    assert "file_version" in vinfo
    assert "tool_version" in vinfo
    
    # Check that file_version matches the spec's version
    assert vinfo["file_version"] == dogmaseq_dig_spec.seqspec_version
    
    # Check that tool_version is a string and not empty
    assert isinstance(vinfo["tool_version"], str)
    assert len(vinfo["tool_version"]) > 0


def test_format_version():
    """Test format_version function"""
    # Test with sample version info
    vinfo = {
        "file_version": "0.3.0",
        "tool_version": "1.2.3"
    }
    
    formatted = format_version(vinfo)
    
    # Check the formatted output
    expected_lines = [
        "seqspec version: 1.2.3",
        "seqspec file version: 0.3.0"
    ]
    
    lines = formatted.split('\n')
    assert len(lines) == 2
    assert lines[0] == expected_lines[0]
    assert lines[1] == expected_lines[1]


def test_seqspec_version_with_dogmaseq_spec(dogmaseq_dig_spec: Assay):
    """Test the complete version workflow with dogmaseq spec"""
    # Get version info
    vinfo = seqspec_version(dogmaseq_dig_spec)
    
    # Format it
    formatted = format_version(vinfo)
    
    # Check that the formatted output contains both versions
    assert "seqspec version:" in formatted
    assert "seqspec file version:" in formatted
    assert dogmaseq_dig_spec.seqspec_version in formatted
    
    # Check that tool_version is present and not empty
    assert vinfo["tool_version"] is not None
    assert len(vinfo["tool_version"]) > 0


def test_seqspec_version_structure(dogmaseq_dig_spec: Assay):
    """Test that the version info has the correct structure and types"""
    vinfo = seqspec_version(dogmaseq_dig_spec)
    
    # Check types
    assert isinstance(vinfo, dict)
    assert isinstance(vinfo["file_version"], str)
    assert isinstance(vinfo["tool_version"], str)
    
    # Check that versions are not empty
    assert len(vinfo["file_version"]) > 0
    assert len(vinfo["tool_version"]) > 0
    
    # Check that file_version matches the spec
    assert vinfo["file_version"] == dogmaseq_dig_spec.seqspec_version 
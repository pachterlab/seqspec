import pytest
from seqspec.Region import (
    Region, RegionInput, Onlist, OnlistInput, RegionCoordinate,
    RegionCoordinateDifference, SequenceType, RegionType,
    project_regions_to_coordinates, itx_read,
    complement_nucleotide, complement_sequence
)

def test_region_creation_minimal():
    """Test creating a minimal region"""
    region = Region(
        region_id="test_region",
        region_type="barcode",
        name="Test Barcode",
        sequence_type="onlist",
    )
    assert region.region_id == "test_region"
    assert region.region_type == "barcode"
    assert region.name == "Test Barcode"
    assert region.sequence_type == "onlist"
    assert region.sequence == ""
    assert region.min_len == 0
    assert region.max_len == 1024
    assert region.onlist is None
    assert region.regions == []

def test_region_creation_with_all_fields():
    """Test creating a region with all fields"""
    onlist = Onlist(
        file_id="test_file",
        filename="barcodes.txt",
        filetype="txt",
        filesize=1000,
        url="file://barcodes.txt",
        urltype="local",
        md5="d41d8cd98f00b204e9800998ecf8427e"
    )
    
    region = Region(
        region_id="test_region",
        region_type="barcode",
        name="Test Barcode",
        sequence_type="onlist",
        sequence="NNNNNN",
        min_len=6,
        max_len=6,
        onlist=onlist,
        regions=[]
    )
    
    assert region.region_id == "test_region"
    assert region.region_type == "barcode"
    assert region.name == "Test Barcode"
    assert region.sequence_type == "onlist"
    assert region.sequence == "NNNNNN"
    assert region.min_len == 6
    assert region.max_len == 6
    assert region.onlist == onlist
    assert region.regions == []

def test_region_enum_types():
    """Test region creation with enum types"""
    region = Region(
        region_id="test_region",
        region_type=RegionType.BARCODE,
        name="Test Barcode",
        sequence_type=SequenceType.ONLIST
    )
    assert region.region_type == RegionType.BARCODE
    assert region.sequence_type == SequenceType.ONLIST

def test_region_get_sequence_simple():
    """Test get_sequence for simple region"""
    region = Region(
        region_id="test_region",
        region_type="barcode",
        name="Test Barcode",
        sequence_type="fixed",
        sequence="ATCG"
    )
    assert region.get_sequence() == "ATCG"

def test_region_get_sequence_nested():
    """Test get_sequence for nested regions"""
    child1 = Region(
        region_id="child1",
        region_type="barcode",
        name="Child 1",
        sequence_type="fixed",
        sequence="AT"
    )
    child2 = Region(
        region_id="child2",
        region_type="linker",
        name="Child 2",
        sequence_type="fixed",
        sequence="CG"
    )
    
    parent = Region(
        region_id="parent",
        region_type="joined",
        name="Parent",
        sequence_type="joined",
        regions=[child1, child2]
    )
    
    assert parent.get_sequence() == "ATCG"

def test_region_get_len_simple():
    """Test get_len for simple region"""
    region = Region(
        region_id="test_region",
        region_type="barcode",
        name="Test Barcode",
        sequence_type="fixed",
        sequence="ATCG",
        min_len=4,
        max_len=4
    )
    min_len, max_len = region.get_len()
    assert min_len == 4
    assert max_len == 4

def test_region_get_len_nested():
    """Test get_len for nested regions"""
    child1 = Region(
        region_id="child1",
        region_type="barcode",
        name="Child 1",
        sequence_type="fixed",
        sequence="AT",
        min_len=2,
        max_len=2
    )
    child2 = Region(
        region_id="child2",
        region_type="linker",
        name="Child 2",
        sequence_type="fixed",
        sequence="CG",
        min_len=2,
        max_len=2
    )
    
    parent = Region(
        region_id="parent",
        region_type="joined",
        name="Parent",
        sequence_type="joined",
        regions=[child1, child2]
    )
    
    min_len, max_len = parent.get_len()
    assert min_len == 4
    assert max_len == 4

def test_region_update_attr():
    """Test update_attr method"""
    child1 = Region(
        region_id="child1",
        region_type="barcode",
        name="Child 1",
        sequence_type="fixed",
        sequence="AT",
        min_len=2,
        max_len=2
    )
    child2 = Region(
        region_id="child2",
        region_type="linker",
        name="Child 2",
        sequence_type="fixed",
        sequence="CG",
        min_len=2,
        max_len=2
    )
    
    parent = Region(
        region_id="parent",
        region_type="joined",
        name="Parent",
        sequence_type="joined",
        regions=[child1, child2]
    )
    
    parent.update_attr()
    assert parent.sequence == "ATCG"
    assert parent.min_len == 4
    assert parent.max_len == 4

def test_region_update_attr_random():
    """Test update_attr with random sequence type"""
    region = Region(
        region_id="test_region",
        region_type="random",
        name="Random Region",
        sequence_type="random",
        min_len=10,
        max_len=10
    )
    
    region.update_attr()
    assert region.sequence == "X" * 10

def test_region_update_attr_onlist():
    """Test update_attr with onlist sequence type"""
    region = Region(
        region_id="test_region",
        region_type="barcode",
        name="Barcode Region",
        sequence_type="onlist",
        min_len=6,
        max_len=6
    )
    
    region.update_attr()
    assert region.sequence == "N" * 6

def test_region_get_region_by_id():
    """Test get_region_by_id method"""
    child1 = Region(
        region_id="child1",
        region_type="barcode",
        name="Child 1",
        sequence_type="fixed",
        sequence="AT"
    )
    child2 = Region(
        region_id="child2",
        region_type="linker",
        name="Child 2",
        sequence_type="fixed",
        sequence="CG"
    )
    
    parent = Region(
        region_id="parent",
        region_type="joined",
        name="Parent",
        sequence_type="joined",
        regions=[child1, child2]
    )
    
    # Test finding existing regions
    found = parent.get_region_by_id("child1")
    assert len(found) == 1
    assert found[0] == child1
    
    found = parent.get_region_by_id("child2")
    assert len(found) == 1
    assert found[0] == child2
    
    found = parent.get_region_by_id("parent")
    assert len(found) == 1
    assert found[0] == parent
    
    # Test finding non-existent region
    found = parent.get_region_by_id("non_existent")
    assert len(found) == 0

def test_region_get_region_by_region_type():
    """Test get_region_by_region_type method"""
    child1 = Region(
        region_id="child1",
        region_type="barcode",
        name="Child 1",
        sequence_type="fixed",
        sequence="AT"
    )
    child2 = Region(
        region_id="child2",
        region_type="linker",
        name="Child 2",
        sequence_type="fixed",
        sequence="CG"
    )
    child3 = Region(
        region_id="child3",
        region_type="barcode",
        name="Child 3",
        sequence_type="fixed",
        sequence="GC"
    )
    
    parent = Region(
        region_id="parent",
        region_type="joined",
        name="Parent",
        sequence_type="joined",
        regions=[child1, child2, child3]
    )
    
    # Test finding regions by type
    found = parent.get_region_by_region_type("barcode")
    assert len(found) == 2
    assert child1 in found
    assert child3 in found
    
    found = parent.get_region_by_region_type("linker")
    assert len(found) == 1
    assert found[0] == child2
    
    found = parent.get_region_by_region_type("joined")
    assert len(found) == 1
    assert found[0] == parent

def test_region_get_onlist_regions():
    """Test get_onlist_regions method"""
    onlist = Onlist(
        file_id="test_file",
        filename="barcodes.txt",
        filetype="txt",
        filesize=1000,
        url="file://barcodes.txt",
        urltype="local",
        md5="d41d8cd98f00b204e9800998ecf8427e"
    )
    
    child1 = Region(
        region_id="child1",
        region_type="barcode",
        name="Child 1",
        sequence_type="onlist",
        onlist=onlist
    )
    child2 = Region(
        region_id="child2",
        region_type="linker",
        name="Child 2",
        sequence_type="fixed",
        sequence="CG"
    )
    
    parent = Region(
        region_id="parent",
        region_type="joined",
        name="Parent",
        sequence_type="joined",
        regions=[child1, child2]
    )
    
    found = parent.get_onlist_regions()
    assert len(found) == 1
    assert found[0] == child1

def test_region_get_leaves():
    """Test get_leaves method"""
    child1 = Region(
        region_id="child1",
        region_type="barcode",
        name="Child 1",
        sequence_type="fixed",
        sequence="AT"
    )
    child2 = Region(
        region_id="child2",
        region_type="linker",
        name="Child 2",
        sequence_type="fixed",
        sequence="CG"
    )
    
    parent = Region(
        region_id="parent",
        region_type="joined",
        name="Parent",
        sequence_type="joined",
        regions=[child1, child2]
    )
    
    leaves = parent.get_leaves()
    assert len(leaves) == 2
    assert child1 in leaves
    assert child2 in leaves

def test_region_get_leaf_region_types():
    """Test get_leaf_region_types method"""
    child1 = Region(
        region_id="child1",
        region_type="barcode",
        name="Child 1",
        sequence_type="fixed",
        sequence="AT",
        regions=[]
    )
    child2 = Region(
        region_id="child2",
        region_type="linker",
        name="Child 2",
        sequence_type="fixed",
        sequence="CG",
        regions=[]
    )
    child3 = Region(
        region_id="child3",
        region_type="barcode",
        name="Child 3",
        sequence_type="fixed",
        sequence="GC",
        regions=[]
    )
    
    parent = Region(
        region_id="parent",
        region_type="joined",
        name="Parent",
        sequence_type="joined",
        regions=[child1, child2, child3]
    )
    
    types = parent.get_leaf_region_types()
    assert types == {"barcode", "linker"}

def test_region_to_newick():
    """Test to_newick method"""
    child1 = Region(
        region_id="child1",
        region_type="barcode",
        name="Child 1",
        sequence_type="fixed",
        sequence="AT",
        min_len=2,
        max_len=2,
        regions=[]
    )
    child2 = Region(
        region_id="child2",
        region_type="linker",
        name="Child 2",
        sequence_type="fixed",
        sequence="CG",
        min_len=2,
        max_len=2,
        regions=[]
    )
    
    parent = Region(
        region_id="parent",
        region_type="joined",
        name="Parent",
        sequence_type="joined",
        regions=[child1, child2]
    )
    
    newick = parent.to_newick()
    # Should contain both child regions and parent
    assert "child1" in newick
    assert "child2" in newick
    assert "parent" in newick

def test_region_reverse():
    """Test reverse method"""
    region = Region(
        region_id="test_region",
        region_type="barcode",
        name="Test Barcode",
        sequence_type="fixed",
        sequence="ATCG",
        regions=[]
    )
    
    region.reverse()
    assert region.sequence == "GCTA"

def test_region_complement():
    """Test complement method"""
    region = Region(
        region_id="test_region",
        region_type="barcode",
        name="Test Barcode",
        sequence_type="fixed",
        sequence="ATCG",
        regions=[]
    )
    
    region.complement()
    assert region.sequence == "TAGC"

def test_region_input():
    """Test RegionInput creation and conversion."""
    onlist_input = OnlistInput(
        file_id="test_file",
        filename="test.txt",
        filetype="text",
        filesize=100,
        url="file://test.txt",
        urltype="local",
        md5="d41d8cd98f00b204e9800998ecf8427e"
    )
    
    region_input = RegionInput(
        region_id="test_region",
        region_type="barcode",
        name="Test Barcode",
        sequence_type="onlist",
        sequence="NNNNNN",
        min_len=6,
        max_len=6,
        onlist=onlist_input
    )
    
    region = region_input.to_region()
    assert region.region_id == "test_region"
    assert region.region_type == "barcode"
    assert region.name == "Test Barcode"
    assert region.sequence_type == "onlist"
    assert region.sequence == "NNNNNN"
    assert region.min_len == 6
    assert region.max_len == 6
    assert region.onlist is not None
    assert region.onlist.file_id == "test_file"
    assert region.regions == []

def test_onlist_creation():
    """Test Onlist creation"""
    onlist = Onlist(
        file_id="test_file",
        filename="barcodes.txt",
        filetype="txt",
        filesize=1000,
        url="file://barcodes.txt",
        urltype="local",
        md5="d41d8cd98f00b204e9800998ecf8427e"
    )
    
    assert onlist.file_id == "test_file"
    assert onlist.filename == "barcodes.txt"
    assert onlist.filetype == "txt"
    assert onlist.filesize == 1000
    assert onlist.url == "file://barcodes.txt"
    assert onlist.urltype == "local"
    assert onlist.md5 == "d41d8cd98f00b204e9800998ecf8427e"

def test_onlist_input():
    """Test OnlistInput class"""
    onlist_input = OnlistInput(
        file_id="test_file",
        filename="barcodes.txt",
        filetype="txt",
        filesize=1000,
        url="file://barcodes.txt",
        urltype="local",
        md5="d41d8cd98f00b204e9800998ecf8427e"
    )
    
    onlist = onlist_input.to_onlist()
    assert onlist.file_id == "test_file"
    assert onlist.filename == "barcodes.txt"
    assert onlist.filetype == "txt"
    assert onlist.filesize == 1000
    assert onlist.url == "file://barcodes.txt"
    assert onlist.urltype == "local"
    assert onlist.md5 == "d41d8cd98f00b204e9800998ecf8427e"

def test_region_coordinate_creation():
    """Test RegionCoordinate creation"""
    coord = RegionCoordinate(
        region_id="test_region",
        region_type="barcode",
        name="Test Barcode",
        sequence_type="fixed",
        sequence="ATCG",
        start=0,
        stop=4
    )
    
    assert coord.region_id == "test_region"
    assert coord.start == 0
    assert coord.stop == 4

def test_region_coordinate_str():
    """Test RegionCoordinate string representation."""
    coord = RegionCoordinate(
        region_id="test_region",
        region_type="barcode",
        name="Test Barcode",
        sequence_type="fixed",
        sequence="ATCG",
        min_len=0,
        max_len=1024,
        start=0,
        stop=4
    )
    coord_str = str(coord)
    assert "Test Barcode" in coord_str
    assert "[0, 4)" in coord_str

def test_region_coordinate_subtraction():
    """Test RegionCoordinate subtraction."""
    coord1 = RegionCoordinate(
        region_id="test_region1",
        region_type="barcode",
        name="Test Barcode 1",
        sequence_type="fixed",
        sequence="ATCG",
        min_len=0,
        max_len=1024,
        start=0,
        stop=4
    )
    coord2 = RegionCoordinate(
        region_id="test_region2",
        region_type="barcode",
        name="Test Barcode 2",
        sequence_type="fixed",
        sequence="ATCG",
        min_len=0,
        max_len=1024,
        start=1,
        stop=3
    )
    
    # Test that subtraction raises ValueError as implemented
    with pytest.raises(ValueError, match="Subtraction is not defined"):
        diff = coord1 - coord2

def test_project_regions_to_coordinates():
    """Test project_regions_to_coordinates function"""
    region1 = Region(
        region_id="region1",
        region_type="barcode",
        name="Region 1",
        sequence_type="fixed",
        sequence="AT",
        min_len=2,
        max_len=2,
        regions=[]
    )
    region2 = Region(
        region_id="region2",
        region_type="linker",
        name="Region 2",
        sequence_type="fixed",
        sequence="CG",
        min_len=2,
        max_len=2,
        regions=[]
    )
    
    coords = project_regions_to_coordinates([region1, region2])
    assert len(coords) == 2
    assert coords[0].start == 0
    assert coords[0].stop == 2
    assert coords[1].start == 2
    assert coords[1].stop == 4

def test_itx_read():
    """Test itx_read function"""
    region1 = Region(
        region_id="region1",
        region_type="barcode",
        name="Region 1",
        sequence_type="fixed",
        sequence="AT",
        min_len=2,
        max_len=2,
        regions=[]
    )
    region2 = Region(
        region_id="region2",
        region_type="linker",
        name="Region 2",
        sequence_type="fixed",
        sequence="CG",
        min_len=2,
        max_len=2,
        regions=[]
    )
    
    coords = [
        RegionCoordinate(
            region_id="region1",
            region_type="barcode",
            name="Region 1",
            sequence_type="fixed",
            sequence="AT",
            start=0,
            stop=2
        ),
        RegionCoordinate(
            region_id="region2",
            region_type="linker",
            name="Region 2",
            sequence_type="fixed",
            sequence="CG",
            start=2,
            stop=4
        )
    ]
    
    # Test intersection with read that overlaps both regions
    result = itx_read(coords, 1, 3)
    assert len(result) == 2
    
    # Test intersection with read that only overlaps first region
    result = itx_read(coords, 0, 1)
    assert len(result) == 1
    assert result[0].region_id == "region1"

def test_complement_nucleotide():
    """Test complement_nucleotide function"""
    assert complement_nucleotide('A') == 'T'
    assert complement_nucleotide('T') == 'A'
    assert complement_nucleotide('C') == 'G'
    assert complement_nucleotide('G') == 'C'
    assert complement_nucleotide('N') == 'N'
    assert complement_nucleotide('X') == 'X'

def test_complement_sequence():
    """Test complement_sequence function"""
    assert complement_sequence('ATCG') == 'TAGC'
    assert complement_sequence('NNNN') == 'NNNN'
    assert complement_sequence('') == ''
    assert complement_sequence('ATCGN') == 'TAGCN' 


@pytest.fixture
def rna_lib_spec(dogmaseq_dig_spec):
    """Fixture to get the RNA library spec from the dogmaseq-dig spec"""
    return dogmaseq_dig_spec.get_libspec("rna")

def test_get_sequence_nested_real(rna_lib_spec):
    """Test get_sequence on a real nested region"""
    sequence = rna_lib_spec.get_sequence()
    assert isinstance(sequence, str)
    assert len(sequence) > 0

def test_get_len_nested_real(rna_lib_spec):
    """Test get_len on a real nested region"""
    min_len, max_len = rna_lib_spec.get_len()
    assert isinstance(min_len, int)
    assert isinstance(max_len, int)
    assert max_len >= min_len

def test_update_attr_nested_real(rna_lib_spec):
    """Test update_attr on a real nested region"""
    original_seq = rna_lib_spec.sequence
    original_min_len = rna_lib_spec.min_len
    original_max_len = rna_lib_spec.max_len

    rna_lib_spec.update_attr()

    assert rna_lib_spec.sequence == original_seq
    assert rna_lib_spec.min_len == original_min_len
    assert rna_lib_spec.max_len == original_max_len

def test_get_region_by_id_real(rna_lib_spec):
    """Test get_region_by_id on a real spec"""
    found = rna_lib_spec.get_region_by_id("rna_cell_bc")
    assert len(found) > 0
    assert found[0].region_id == "rna_cell_bc"

def test_get_region_by_type_real(rna_lib_spec):
    """Test get_region_by_region_type on a real spec"""
    found = rna_lib_spec.get_region_by_region_type("cdna")
    assert len(found) > 0
    for region in found:
        assert region.region_type == "cdna"

def test_get_onlist_regions_real(rna_lib_spec):
    """Test get_onlist_regions on a real spec"""
    onlist_regions = rna_lib_spec.get_onlist_regions()
    assert len(onlist_regions) > 0
    for region in onlist_regions:
        assert region.onlist is not None

def test_get_leaves_real(rna_lib_spec):
    """Test get_leaves on a real spec"""
    leaves = rna_lib_spec.get_leaves()
    # print(leaves)
    assert len(leaves) > 0
    for leaf in leaves:
        assert leaf.regions == []

def test_get_leaf_region_types_real(rna_lib_spec):
    """Test get_leaf_region_types on a real spec"""
    types = rna_lib_spec.get_leaf_region_types()
    assert len(types) > 0
    assert "umi" in types
    assert "barcode" in types

def test_to_newick_real(rna_lib_spec):
    """Test to_newick on a real spec"""
    newick = rna_lib_spec.to_newick()
    assert isinstance(newick, str)
    assert newick.startswith("(")
    assert newick.endswith(")rna")

def test_reverse_real(rna_lib_spec):
    """Test reverse method on a real nested region"""
    original_sequence = rna_lib_spec.get_sequence()
    rna_lib_spec.reverse()
    reversed_sequence = rna_lib_spec.get_sequence()
    assert reversed_sequence != original_sequence
    assert len(reversed_sequence) == len(original_sequence)

def test_complement_real(rna_lib_spec):
    """Test complement method on a real nested region"""
    original_sequence = rna_lib_spec.get_sequence()
    rna_lib_spec.complement()
    complemented_sequence = rna_lib_spec.get_sequence()
    assert complement_sequence(original_sequence) == complemented_sequence 
import pytest
from seqspec.Region import (
    Region, RegionInput, Onlist, OnlistInput, RegionCoordinate,
    RegionCoordinateDifference, SequenceType, RegionType,
    project_regions_to_coordinates, itx_read,
    complement_nucleotide, complement_sequence
)
from seqspec.Region import Onlist, OnlistInput, RustOnlist
from seqspec.Region import Region, RegionInput, RustRegion
from seqspec.Region import (
    Region,
    RegionInput,
    Onlist,
    OnlistInput,
    RustRegion,
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


def test_rustonlist_roundtrip_and_mutation():
    # pytest.importorskip("seqspec._core")

    inp = OnlistInput(filename="RNA-737K-arc-v1.txt.gz", url="https://example/file.txt.gz", urltype="https")
    py = inp.to_onlist()
    ro = RustOnlist.from_model(py)

    # Assert parity on all attributes
    assert ro.file_id == py.file_id
    assert ro.filename == py.filename
    assert ro.filetype == py.filetype
    assert ro.filesize == py.filesize
    assert ro.url == py.url
    assert ro.urltype == py.urltype
    assert ro.md5 == py.md5

    # Mutate in Rust and snapshot
    ro.md5 = "deadbeef"
    snap = ro.snapshot()
    assert snap.md5 == "deadbeef"
    assert py.md5 != "deadbeef"  # original DTO unchanged

def test_rustonlist_json_roundtrip():
    # pytest.importorskip("seqspec._core")
    py = Onlist(file_id="ol1", filename="ol.txt", filetype="txt", filesize=10, url="ol.txt", urltype="local", md5="")
    from seqspec._core import Onlist as _CoreOnlist
    assert _CoreOnlist.from_json(py.model_dump_json()).to_json() == py.model_dump_json()

def _make_small_tree() -> Region:
    # parent -> [leafA (AAA, len=3), leafB (TT, len=2)]
    leaf_a = Region(
        region_id="A",
        region_type="named",
        name="A",
        sequence_type="fixed",
        sequence="AAA",
        min_len=3,
        max_len=3,
        onlist=None,
        regions=[],
    )
    leaf_b = Region(
        region_id="B",
        region_type="named",
        name="B",
        sequence_type="fixed",
        sequence="TT",
        min_len=2,
        max_len=2,
        onlist=None,
        regions=[],
    )
    parent = Region(
        region_id="root",
        region_type="named",
        name="root",
        sequence_type="joined",
        sequence="",
        min_len=0,
        max_len=0,
        onlist=None,
        regions=[leaf_a, leaf_b],
    )
    return parent

def test_rustregion_update_and_queries():
    # pytest.importorskip("seqspec._core")

    py = _make_small_tree()
    rr = RustRegion.from_model(py)

    # update derived attributes
    rr.update_attr()
    seq = rr.get_sequence()
    mn, mx = rr.get_len()

    assert seq == "AAATT"
    assert (mn, mx) == (5, 5)

    # leaves & region type set
    leaves = rr.get_leaves()
    assert [r.region_id for r in leaves] == ["A", "B"]
    rtypes = rr.get_leaf_region_types()
    assert "named" in rtypes

    # by id
    found = rr.get_region_by_id("A")
    assert len(found) == 1 and found[0].region_id == "A"

    # newick
    assert rr.to_newick() == "('A:3','B:2')root"

def test_rustregion_reverse_and_complement():
    # pytest.importorskip("seqspec._core")

    py = _make_small_tree()
    rr = RustRegion.from_model(py)
    rr.update_attr()

    rr.reverse()
    snap1 = rr.snapshot()
    # reversing the leaves (AAA -> AAA, TT -> TT) but order preserved in tree;
    # we only reverse per-leaf sequence, not reorder children
    assert snap1.get_leaves()[0].sequence == "AAA"
    assert snap1.get_leaves()[1].sequence == "TT"

    rr.complement()
    snap2 = rr.snapshot()
    # AAA -> TTT, TT -> AA
    assert snap2.get_leaves()[0].sequence == "TTT"
    assert snap2.get_leaves()[1].sequence == "AA"

# ---------- helpers ----------

def _leaf(region_id: str, seq: str, min_len: int | None = None, max_len: int | None = None, rtype: str = "named",
          seqtype: str = "fixed", onlist: Onlist | None = None) -> Region:
    seq = seq or ""
    if min_len is None:
        min_len = len(seq)
    if max_len is None:
        max_len = len(seq)
    return Region(
        region_id=region_id,
        region_type=rtype,
        name=region_id,
        sequence_type=seqtype,
        sequence=seq,
        min_len=min_len,
        max_len=max_len,
        onlist=onlist,
        regions=[],
    )

def _tree_joined(region_id: str, children: list[Region], rtype: str = "named") -> Region:
    return Region(
        region_id=region_id,
        region_type=rtype,
        name=region_id,
        sequence_type="joined",
        sequence="",
        min_len=0,
        max_len=0,
        onlist=None,
        regions=children,
    )

def _simple_tree() -> Region:
    # root -> [A("AAA"), B("TT")]
    A = _leaf("A", "AAA", rtype="named", seqtype="fixed")
    B = _leaf("B", "TT",  rtype="named", seqtype="fixed")
    return _tree_joined("root", [A, B])

def _tree_with_random_onlist() -> Region:
    # root -> [randX (random, min=5), onlistN (onlist, min=3)]
    randX = _leaf("randX", "", min_len=5, max_len=5, seqtype="random", rtype="umi")
    ol = Onlist(file_id="ol1", filename="ol1.txt", filetype="txt", filesize=1, url="ol1.txt", urltype="local", md5="")
    onlN = _leaf("onlistN", "", min_len=3, max_len=3, seqtype="onlist", rtype="barcode", onlist=ol)
    return _tree_joined("root", [randX, onlN])

def _assert_region_equal(py: Region, rust_snap: Region):
    # Basic field equality (not exhaustive)
    assert py.region_id == rust_snap.region_id
    assert str(py.region_type) == str(rust_snap.region_type)
    assert py.name == rust_snap.name
    assert str(py.sequence_type) == str(rust_snap.sequence_type)
    assert py.min_len == rust_snap.min_len
    assert py.max_len == rust_snap.max_len
    assert py.sequence == rust_snap.sequence
    # Check onlist presence equivalence at this node
    if py.onlist is None:
        assert rust_snap.onlist is None
    else:
        assert rust_snap.onlist is not None
        assert py.onlist.filename == rust_snap.onlist.filename


# ---------- tests ----------

def test_update_attr_sequence_and_lengths_fixed_joined():
    # pytest.importorskip("seqspec._core")
    py = _simple_tree()
    # Python behavior
    py.update_attr()
    py_seq = py.get_sequence()
    py_len = py.get_len()

    rr = RustRegion.from_model(py)
    rr.update_attr()
    ru_seq = rr.get_sequence()
    ru_len = rr.get_len()

    assert py_seq == "AAATT"
    assert ru_seq == py_seq
    assert py_len == (5, 5)
    assert ru_len == py_len

    snap = rr.snapshot()
    _assert_region_equal(py, snap)


def test_leaf_queries_and_newick():
    # pytest.importorskip("seqspec._core")
    py = _simple_tree()
    py.update_attr()

    rr = RustRegion.from_model(py)
    rr.update_attr()

    # leaves
    py_leaves = [r.region_id for r in py.get_leaves()]
    ru_leaves = [r.region_id for r in rr.get_leaves()]
    assert py_leaves == ru_leaves == ["A", "B"]

    # region types set (as strings)
    assert set(py.get_leaf_region_types()) == set(rr.get_leaf_region_types())

    # find by id
    py_by_id = [r.region_id for r in py.get_region_by_id("A")]
    ru_by_id = [r.region_id for r in rr.get_region_by_id("A")]
    assert py_by_id == ru_by_id == ["A"]

    # find by region_type
    py_by_type = [r.region_id for r in py.get_region_by_region_type("named")]
    ru_by_type = [r.region_id for r in rr.get_region_by_region_type("named")]
    assert set(py_by_type) == set(ru_by_type)

    # newick
    assert py.to_newick() == rr.to_newick() == "('A:3','B:2')root"


def test_random_and_onlist_behavior():
    # pytest.importorskip("seqspec._core")
    py = _tree_with_random_onlist()
    py.update_attr()
    py_seq = py.get_sequence()
    py_len = py.get_len()

    # Expect: "XXXXX" + "NNN" (random = X*min_len; onlist = N*min_len)
    assert py_seq == "XXXXXNNN"
    assert py_len == (8, 8)

    rr = RustRegion.from_model(py)
    rr.update_attr()
    assert rr.get_sequence() == py_seq
    assert rr.get_len() == py_len

    # onlist regions
    py_ol_ids = [r.region_id for r in py.get_onlist_regions()]
    ru_ol_ids = [r.region_id for r in rr.get_onlist_regions()]
    assert py_ol_ids == ru_ol_ids == ["onlistN"]

    snap = rr.snapshot()
    _assert_region_equal(py, snap)


def test_update_region_by_id_and_update_region():
    # pytest.importorskip("seqspec._core")
    py = _simple_tree()
    py.update_attr()

    rr = RustRegion.from_model(py)
    rr.update_attr()

    # Partial update on leaf A
    rr.update_region_by_id(
        target_region_id="A",
        name="A_renamed",
        min_len=4,
        max_len=4,
        sequence="AAAA",
    )
    # Recompute derived
    rr.update_attr()
    snap = rr.snapshot()

    # Python side apply same change and recompute
    py.update_region_by_id("A", region_id=None, region_type=None, name="A_renamed",
                           sequence_type=None, sequence="AAAA", min_len=4, max_len=4)
    py.update_attr()

    # Parity
    assert snap.get_region_by_id("A")[0].name == "A_renamed"
    assert snap.get_len() == py.get_len()
    assert snap.get_sequence() == py.get_sequence()

    # Now test full update_region on the root node
    rr.update_region(
        region_id="root2",
        region_type="named",
        name="root2",
        sequence_type="joined",
        sequence="",   # joined will be recomputed by update_attr
        min_len=0,
        max_len=0,
        onlist=None,
    )
    rr.update_attr()
    snap2 = rr.snapshot()
    assert snap2.region_id == "root2"
    assert snap2.get_sequence() == py.get_sequence()  # children unchanged
    assert snap2.get_len() == py.get_len()


def test_reverse_and_complement_leaf_sequences():
    # pytest.importorskip("seqspec._core")
    py = _simple_tree()
    py.update_attr()

    rr = RustRegion.from_model(py)
    rr.update_attr()

    # Reverse (per-leaf)
    rr.reverse()
    snap_rev = rr.snapshot()
    # "AAA" -> "AAA", "TT" -> "TT" (palindromic examples; still a structural op)
    assert [r.sequence for r in snap_rev.get_leaves()] == ["AAA", "TT"]

    # Complement (A<->T, C<->G, etc.)
    rr.complement()
    snap_comp = rr.snapshot()
    assert [r.sequence for r in snap_comp.get_leaves()] == ["TTT", "AA"]


def test_get_leaves_with_region_id_behavior():
    # pytest.importorskip("seqspec._core")
    # root -> middle -> [leaf1, leaf2]
    leaf1 = _leaf("leaf1", "AC", rtype="named")
    leaf2 = _leaf("leaf2", "GT", rtype="named")
    middle = Region(
        region_id="middle",
        region_type="named",
        name="middle",
        sequence_type="joined",
        sequence="",
        min_len=0,
        max_len=0,
        onlist=None,
        regions=[leaf1, leaf2],
    )
    root = _tree_joined("root", [middle])

    # Python
    py = root
    py.update_attr()
    py_selected_ids = [r.region_id for r in py.get_leaves_with_region_id("middle")]

    # Rust
    rr = RustRegion.from_model(py)
    rr.update_attr()
    ru_selected_ids = [r.region_id for r in rr.get_leaves_with_region_id("middle")]

    # Your Python logic: if region_id matches, include that node (don’t descend)
    assert py_selected_ids == ["middle"]
    assert ru_selected_ids == ["middle"]


def test_region_get_onlist_method_simple():
    onlist = Onlist(
        file_id="olx",
        filename="ol.txt",
        filetype="txt",
        filesize=1,
        url="ol.txt",
        urltype="local",
        md5="",
    )
    r_with = Region(
        region_id="r1",
        region_type="barcode",
        name="r1",
        sequence_type="onlist",
        min_len=3,
        max_len=3,
        onlist=onlist,
        regions=[],
    )
    r_without = Region(
        region_id="r2",
        region_type="barcode",
        name="r2",
        sequence_type="fixed",
        sequence="AAA",
        min_len=3,
        max_len=3,
        regions=[],
    )
    assert r_with.get_onlist() is onlist
    assert r_without.get_onlist() is None


def test_region_update_region_python():
    r = Region(
        region_id="r",
        region_type="named",
        name="r",
        sequence_type="fixed",
        sequence="AC",
        min_len=2,
        max_len=2,
        regions=[],
    )
    ol = Onlist(
        file_id="ol1",
        filename="ol.txt",
        filetype="txt",
        filesize=1,
        url="ol.txt",
        urltype="local",
        md5="deadbeef",
    )
    r.update_region(
        region_id="r2",
        region_type="barcode",
        name="r2",
        sequence_type="onlist",
        sequence="",
        min_len=3,
        max_len=3,
        onlist=ol,
    )
    r.update_attr()
    assert (r.region_id, r.region_type, r.name) == ("r2", "barcode", "r2")
    assert r.sequence_type == "onlist"
    assert r.sequence == "N" * 3
    assert (r.min_len, r.max_len) == (3, 3)
    assert r.onlist is ol


def test_update_region_by_id_partial_none():
    leaf = Region(
        region_id="L",
        region_type="named",
        name="L",
        sequence_type="fixed",
        sequence="GG",
        min_len=2,
        max_len=2,
        regions=[],
    )
    root = Region(
        region_id="root",
        region_type="named",
        name="root",
        sequence_type="joined",
        regions=[leaf],
    )
    root.update_region_by_id(
        target_region_id="L",
        region_id=None,  # keep the same
        region_type=None,
        name="L2",  # change only name
        sequence_type=None,
        sequence=None,
        min_len=None,
        max_len=None,
    )
    root.update_attr()
    updated = root.get_region_by_id("L")[0]
    assert updated.name == "L2"
    assert updated.region_id == "L"
    assert updated.sequence == "GG"
    assert updated.min_len == 2 and updated.max_len == 2


def test_region_repr_contains_type_and_lengths():
    r = Region(
        region_id="x",
        region_type="named",
        name="x",
        sequence_type="fixed",
        sequence="A",
        min_len=1,
        max_len=1,
        regions=[],
    )
    s = repr(r)
    assert "named" in s
    assert "(1, 1)" in s


def test_get_region_by_region_type_with_enum():
    r_leaf = Region(
        region_id="e",
        region_type=RegionType.NAMED,
        name="e",
        sequence_type=SequenceType.FIXED,
        sequence="T",
        min_len=1,
        max_len=1,
        regions=[],
    )
    r_root = Region(
        region_id="root",
        region_type=RegionType.NAMED,
        name="root",
        sequence_type=SequenceType.JOINED,
        regions=[r_leaf],
    )
    found = r_root.get_region_by_region_type(RegionType.NAMED)
    assert len(found) >= 2
    assert any(x.region_id == "e" for x in found)


def test_regioncoordinate_subtraction_scenarios():
    a = RegionCoordinate(
        region_id="a",
        region_type="named",
        name="a",
        sequence_type="fixed",
        sequence="AAAA",
        min_len=0,
        max_len=1024,
        start=0,
        stop=4,
    )
    b = RegionCoordinate(
        region_id="b",
        region_type="named",
        name="b",
        sequence_type="fixed",
        sequence="TT",
        min_len=0,
        max_len=1024,
        start=6,
        stop=8,
    )
    c = a - b
    assert isinstance(c, RegionCoordinate)
    assert c.region_type == "difference"
    assert (c.start, c.stop) == (4, 6)
    assert c.sequence == "X" * (c.stop - c.start)

    # Equal ranges
    x = RegionCoordinate(region_id="x", region_type="named", name="x", sequence_type="fixed", sequence="",
                         min_len=0, max_len=0, start=10, stop=12)
    y = RegionCoordinate(region_id="y", region_type="named", name="y", sequence_type="fixed", sequence="",
                         min_len=0, max_len=0, start=10, stop=12)
    z = x - y
    assert (z.start, z.stop) == (10, 12)


def test_regioncoordinate_difference_loc_field():
    obj = RegionCoordinate(region_id="obj", region_type="named", name="obj", sequence_type="fixed", sequence="",
                           min_len=0, max_len=0, start=0, stop=2)
    fixed = RegionCoordinate(region_id="fixed", region_type="named", name="fixed", sequence_type="fixed", sequence="",
                             min_len=0, max_len=0, start=5, stop=7)
    diff = RegionCoordinateDifference(obj=obj, fixed=fixed, rgncdiff=obj)
    assert diff.loc == "-"

    obj2 = RegionCoordinate(region_id="obj2", region_type="named", name="obj2", sequence_type="fixed", sequence="",
                            min_len=0, max_len=0, start=8, stop=9)
    diff2 = RegionCoordinateDifference(obj=obj2, fixed=fixed, rgncdiff=obj2)
    assert diff2.loc == "+"


def test_to_newick_ignores_n_param():
    A = _leaf("A", "AA")
    B = _leaf("B", "T")
    root = _tree_joined("root", [A, B])
    s1 = root.to_newick()
    s2 = root.to_newick(n="ignored")
    assert s1 == s2


def test_rustonlist_new_and_snapshot():
    ro = RustOnlist.new(file_id="id", filename="f.txt", filetype="txt", filesize=1, url="f.txt", urltype="local", md5="m")
    snap = ro.snapshot()
    assert snap.file_id == "id" and snap.filename == "f.txt"


def test_rustregion_get_and_set_onlist():
    # root carries onlist
    ol = Onlist(file_id="ol1", filename="ol.txt", filetype="txt", filesize=1, url="ol.txt", urltype="local", md5="a")
    root = Region(
        region_id="root",
        region_type="named",
        name="root",
        sequence_type="joined",
        onlist=ol,
        regions=[_leaf("L", "AC")],
    )
    rr = RustRegion.from_model(root)
    got = rr.get_onlist()
    assert got is not None and got.filename == "ol.txt"

    # mutate onlist via Rust proxy
    rr.onlist = RustOnlist.new(file_id="ol2", filename="x.txt", filetype="txt", filesize=2, url="x.txt", urltype="local", md5="b")
    snap = rr.snapshot()
    assert snap.onlist is not None and snap.onlist.filename == "x.txt"


def test_region_rust_parity_sweep():
    # Build a slightly complex tree mixing fixed, random, onlist, and a nested joined
    ol = Onlist(file_id="olX", filename="olx.txt", filetype="txt", filesize=1, url="olx.txt", urltype="local", md5="")
    fixA = _leaf("fixA", "AAA", rtype="barcode", seqtype="fixed")
    rand2 = _leaf("rand2", "", min_len=2, max_len=2, rtype="umi", seqtype="random")
    fx2 = _leaf("fx2", "GC", rtype="linker", seqtype="fixed")
    mid = _tree_joined("mid", [fx2])
    olN = _leaf("olN", "", min_len=3, max_len=3, rtype="barcode", seqtype="onlist", onlist=ol)
    py = _tree_joined("root", [fixA, rand2, mid, olN])

    # Python baseline
    py.update_attr()
    py_seq = py.get_sequence()
    py_len = py.get_len()

    # Rust baseline
    rr = RustRegion.from_model(py)
    rr.update_attr()
    ru_seq = rr.get_sequence()
    ru_len = rr.get_len()

    # Parity on primary derived attributes
    assert ru_seq == py_seq
    assert ru_len == py_len

    # Parity on queries
    assert [r.region_id for r in rr.get_leaves()] == [r.region_id for r in py.get_leaves()]
    assert set(rr.get_leaf_region_types()) == set(py.get_leaf_region_types())
    assert [r.region_id for r in rr.get_onlist_regions()] == [r.region_id for r in py.get_onlist_regions()]
    assert [r.region_id for r in rr.get_region_by_id("mid")] == [r.region_id for r in py.get_region_by_id("mid")]
    assert set(r.region_id for r in rr.get_region_by_region_type("barcode")) == set(
        r.region_id for r in py.get_region_by_region_type("barcode")
    )
    assert rr.to_newick() == py.to_newick()

    # Snapshot parity against the Python DTO
    assert rr.snapshot().model_dump_json() == py.model_dump_json()

    # Mutate a leaf via both APIs and recheck parity
    # Change fixA to sequence AAAA, length 4
    rr.update_region_by_id(
        target_region_id="fixA", name="fixA2", sequence="AAAA", min_len=4, max_len=4
    )
    py.update_region_by_id("fixA", region_id=None, region_type=None, name="fixA2", sequence_type=None, sequence="AAAA", min_len=4, max_len=4)
    rr.update_attr()
    py.update_attr()

    assert rr.get_sequence() == py.get_sequence()
    assert rr.get_len() == py.get_len()
    assert rr.to_newick() == py.to_newick()
    assert rr.snapshot().model_dump_json() == py.model_dump_json()

    # Reverse and complement both sides and verify parity remains
    rr.reverse(); py.reverse()
    rr.update_attr(); py.update_attr()
    assert rr.get_sequence() == py.get_sequence()
    assert rr.get_len() == py.get_len()

    rr.complement(); py.complement()
    rr.update_attr(); py.update_attr()
    assert rr.get_sequence() == py.get_sequence()
    assert rr.get_len() == py.get_len()
    assert rr.snapshot().model_dump_json() == py.model_dump_json()
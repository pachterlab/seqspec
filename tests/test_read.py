import pytest
from seqspec.Read import Read, ReadInput, ReadCoordinate, RustRead
from seqspec.File import File, FileInput, RustFile
from seqspec.Region import RegionCoordinate


def test_read_creation_minimal():
    """Test creating a minimal read"""
    read = Read(
        read_id="test_read",
        name="Test Read",
        modality="RNA",
        primer_id="test_primer",
        min_len=100,
        max_len=150,
        strand="pos"
    )
    assert read.read_id == "test_read"
    assert read.name == "Test Read"
    assert read.modality == "RNA"
    assert read.primer_id == "test_primer"
    assert read.min_len == 100
    assert read.max_len == 150
    assert read.strand == "pos"
    assert read.files == []

def test_read_creation_with_files():
    """Test creating a read with files"""
    file1 = File(
        file_id="file1",
        filename="read1.fastq.gz",
        filetype="fastq",
        filesize=1000000,
        url="file://read1.fastq.gz",
        urltype="local",
        md5="d41d8cd98f00b204e9800998ecf8427e"
    )
    file2 = File(
        file_id="file2",
        filename="read2.fastq.gz",
        filetype="fastq",
        filesize=1000000,
        url="file://read2.fastq.gz",
        urltype="local",
        md5="d41d8cd98f00b204e9800998ecf8427e"
    )
    
    read = Read(
        read_id="test_read",
        name="Test Read",
        modality="RNA",
        primer_id="test_primer",
        min_len=100,
        max_len=150,
        strand="pos",
        files=[file1, file2]
    )
    
    assert len(read.files) == 2
    assert read.files[0].file_id == "file1"
    assert read.files[1].file_id == "file2"

def test_read_set_files():
    """Test set_files method"""
    read = Read(
        read_id="test_read",
        name="Test Read",
        modality="RNA",
        primer_id="test_primer",
        min_len=100,
        max_len=150,
        strand="pos"
    )
    
    file1 = File(
        file_id="file1",
        filename="read1.fastq.gz",
        filetype="fastq",
        filesize=1000000,
        url="file://read1.fastq.gz",
        urltype="local",
        md5="d41d8cd98f00b204e9800998ecf8427e"
    )
    
    read.set_files([file1])
    assert len(read.files) == 1
    assert read.files[0].file_id == "file1"

def test_read_update_read_by_id():
    """Test update_read_by_id method"""
    read = Read(
        read_id="test_read",
        name="Test Read",
        modality="RNA",
        primer_id="test_primer",
        min_len=100,
        max_len=150,
        strand="pos"
    )
    
    # Update some fields
    read.update_read_by_id(
        read_id="updated_read",
        name="Updated Read",
        modality="DNA",
        primer_id="updated_primer",
        min_len=200,
        max_len=250,
        strand="neg"
    )
    
    assert read.read_id == "updated_read"
    assert read.name == "Updated Read"
    assert read.modality == "DNA"
    assert read.primer_id == "updated_primer"
    assert read.min_len == 200
    assert read.max_len == 250
    assert read.strand == "neg"

def test_read_update_read_by_id_partial():
    """Test update_read_by_id with partial updates"""
    read = Read(
        read_id="test_read",
        name="Test Read",
        modality="RNA",
        primer_id="test_primer",
        min_len=100,
        max_len=150,
        strand="pos"
    )
    
    # Update only some fields
    read.update_read_by_id(
        read_id="updated_read",
        name="Updated Read"
    )
    
    assert read.read_id == "updated_read"
    assert read.name == "Updated Read"
    assert read.modality == "RNA"  # Unchanged
    assert read.primer_id == "test_primer"  # Unchanged
    assert read.min_len == 100  # Unchanged
    assert read.max_len == 150  # Unchanged
    assert read.strand == "pos"  # Unchanged

def test_read_get_read_by_file_id():
    """Test getting read by file ID."""
    file1 = File(
        file_id="file1",
        filename="read1.fastq.gz",
        filetype="fastq",
        filesize=1000000,
        url="file://read1.fastq.gz",
        urltype="local",
        md5="d41d8cd98f00b204e9800998ecf8427e"
    )
    
    read = Read(
        read_id="test_read",
        name="Test Read",
        modality="RNA",
        primer_id="test_primer",
        min_len=100,
        max_len=150,
        strand="pos",
        files=[file1]
    )
    
    # Test finding existing file
    found_read = read.get_read_by_file_id("file1")
    assert found_read == read
    
    # Test finding non-existent file
    found_read = read.get_read_by_file_id("nonexistent")
    assert found_read is None

def test_read_repr():
    """Test __repr__ method"""
    read = Read(
        read_id="test_read",
        name="Test Read",
        modality="RNA",
        primer_id="test_primer",
        min_len=100,
        max_len=150,
        strand="pos"
    )
    
    repr_str = repr(read)
    assert "+(100, 150)test_read:test_primer" == repr_str


def test_read_coordinate_creation():
    """Test ReadCoordinate creation"""
    read = Read(
        read_id="test_read",
        name="Test Read",
        modality="RNA",
        primer_id="test_primer",
        min_len=100,
        max_len=150,
        strand="pos"
    )
    
    region_coord1 = RegionCoordinate(
        region_id="region1",
        region_type="barcode",
        name="Region 1",
        sequence_type="fixed",
        sequence="AT",
        start=0,
        stop=2
    )
    region_coord2 = RegionCoordinate(
        region_id="region2",
        region_type="linker",
        name="Region 2",
        sequence_type="fixed",
        sequence="CG",
        start=2,
        stop=4
    )
    
    read_coord = ReadCoordinate(
        read=read,
        rcv=[region_coord1, region_coord2]
    )
    
    assert read_coord.read == read
    assert len(read_coord.rcv) == 2
    assert read_coord.rcv[0] == region_coord1
    assert read_coord.rcv[1] == region_coord2



def test_file_creation():
    """Test File creation"""
    file_obj = File(
        file_id="file1",
        filename="read1.fastq.gz",
        filetype="fastq",
        filesize=1000000,
        url="file://read1.fastq.gz",
        urltype="local",
        md5="d41d8cd98f00b204e9800998ecf8427e"
    )
    
    assert file_obj.file_id == "file1"
    assert file_obj.filename == "read1.fastq.gz"
    assert file_obj.filetype == "fastq"
    assert file_obj.filesize == 1000000
    assert file_obj.url == "file://read1.fastq.gz"
    assert file_obj.urltype == "local"
    assert file_obj.md5 == "d41d8cd98f00b204e9800998ecf8427e"




@pytest.fixture
def atac_r1_read(dogmaseq_dig_spec):
    """Fixture to get the atac_R1 read from the dogmaseq-dig spec"""
    return dogmaseq_dig_spec.get_read("atac_R1")

def test_read_properties_real(atac_r1_read):
    """Test the properties of a Read object from a real spec"""
    assert atac_r1_read.read_id == "atac_R1"
    assert atac_r1_read.name == "atac Read 1"
    assert atac_r1_read.modality == "atac"
    assert atac_r1_read.primer_id == "atac_truseq_read1"
    assert atac_r1_read.min_len == 53
    assert atac_r1_read.max_len == 53
    assert atac_r1_read.strand == "pos"

def test_read_files_real(atac_r1_read):
    """Test the files associated with a Read object from a real spec"""
    assert isinstance(atac_r1_read.files, list)
    assert len(atac_r1_read.files) > 0
    for f in atac_r1_read.files:
        assert isinstance(f, File)
        assert f.filetype == "fastq"

def test_get_read_by_file_id_real(atac_r1_read):
    """Test get_read_by_file_id on a real Read object"""
    # Assumes the file ID exists in the test data
    file_id = atac_r1_read.files[0].file_id
    found_read = atac_r1_read.get_read_by_file_id(file_id)
    assert found_read is not None
    assert found_read.read_id == atac_r1_read.read_id

    # Test with a non-existent file ID
    assert atac_r1_read.get_read_by_file_id("non_existent_file") is None

def test_update_read_by_id_real(atac_r1_read):
    """Test update_read_by_id on a real Read object"""
    atac_r1_read.update_read_by_id(
        name="Updated ATAC Read",
        min_len=55,
        max_len=55
    )
    assert atac_r1_read.name == "Updated ATAC Read"
    assert atac_r1_read.min_len == 55
    assert atac_r1_read.max_len == 55
    # Ensure other properties are unchanged
    assert atac_r1_read.read_id == "atac_R1"
    assert atac_r1_read.modality == "atac" 

def test_rustread_roundtrip_and_mutation():
    pytest.importorskip("seqspec._core")

    r = ReadInput(
        read_id="R1", name="read1", modality="rna", primer_id="truseq_r1",
        min_len=1, max_len=100, strand="pos",
        files=[FileInput(filename="r1.fastq.gz")]
    ).to_read()

    rr = RustRead.from_model(r)

    # parity: check all attributes
    assert rr.read_id == r.read_id
    assert rr.name == r.name
    assert rr.modality == r.modality
    assert rr.primer_id == r.primer_id
    assert rr.min_len == r.min_len
    assert rr.max_len == r.max_len
    assert rr.strand == r.strand
    assert len(rr.files) == len(r.files)
    for rf, f in zip(rr.files, r.files):
        assert rf.file_id == f.file_id
        assert rf.filename == f.filename
        assert rf.filetype == f.filetype
        assert rf.filesize == f.filesize
        assert rf.url == f.url
        assert rf.urltype == f.urltype
        assert rf.md5 == f.md5

    # mutate via Rust and snapshot back
    rr.update_read_by_id(name="renamed", max_len=120, read_id=None, modality=None, primer_id=None,
                         min_len=None, strand=None, files=None)
    snap = rr.snapshot()
    assert snap.name == "renamed"
    assert snap.max_len == 120
    # original DTO unchanged
    assert r.name != "renamed"

def test_rustread_get_by_file_id(dogmaseq_dig_spec):
    pytest.importorskip("seqspec._core")
    r = dogmaseq_dig_spec.get_seqspec("rna")[0]
    rr = RustRead.from_model(r)
    found = rr.get_read_by_file_id(r.files[0].file_id)
    assert found is not None
    assert found.read_id == r.read_id


def test_rustread_new_and_snapshot_parity_with_python():
    pytest.importorskip("seqspec._core")

    # Build Python DTO via inputs
    f1 = FileInput(filename="r1.fastq.gz").to_file()
    f2 = FileInput(filename="r2.fastq.gz").to_file()
    py = ReadInput(
        read_id="R1",
        name="read1",
        modality="rna",
        primer_id="truseq_r1",
        min_len=50,
        max_len=75,
        strand="pos",
        files=[FileInput(filename=f1.filename), FileInput(filename=f2.filename)],
    ).to_read()

    # Build Rust proxy using RustFile list
    rf1 = RustFile.new(file_id=f1.file_id, filename=f1.filename, filetype=f1.filetype, filesize=f1.filesize, url=f1.url, urltype=f1.urltype, md5=f1.md5)
    rf2 = RustFile.new(file_id=f2.file_id, filename=f2.filename, filetype=f2.filetype, filesize=f2.filesize, url=f2.url, urltype=f2.urltype, md5=f2.md5)
    rr = RustRead.new(
        read_id=py.read_id,
        name=py.name,
        modality=py.modality,
        primer_id=py.primer_id,
        min_len=py.min_len,
        max_len=py.max_len,
        strand=py.strand,
        files=[rf1, rf2],
    )

    snap = rr.snapshot()
    assert snap.model_dump_json() == py.model_dump_json()
    assert repr(snap) == repr(py)


def test_read_rust_parity_sweep():
    pytest.importorskip("seqspec._core")

    # Base Python object with one file
    f = FileInput(filename="sample_R1.fastq.gz").to_file()
    py = ReadInput(
        read_id="R1",
        name="read1",
        modality="rna",
        primer_id="truseq_r1",
        min_len=100,
        max_len=150,
        strand="pos",
        files=[FileInput(filename=f.filename)],
    ).to_read()

    # Rust mirror
    rr = RustRead.from_model(py)

    # Parity on attributes and repr
    snap0 = rr.snapshot()
    assert snap0.model_dump_json() == py.model_dump_json()
    assert repr(snap0) == repr(py)

    # Update a subset of fields on both sides and re-check parity
    rr.update_read_by_id(name="renamed", min_len=120, max_len=160, strand="neg",
                         read_id=None, modality=None, primer_id=None, files=None)
    py.update_read_by_id(name="renamed", min_len=120, max_len=160, strand="neg")

    snap1 = rr.snapshot()
    assert snap1.model_dump_json() == py.model_dump_json()
    assert repr(snap1) == repr(py)

    # Query by file id parity (present/absent)
    rr_found = rr.get_read_by_file_id(f.file_id)
    py_found = py.get_read_by_file_id(f.file_id)
    assert rr_found is not None and py_found is not None
    assert rr_found.read_id == py_found.read_id
    assert rr.get_read_by_file_id("does_not_exist") is None
    assert py.get_read_by_file_id("does_not_exist") is None
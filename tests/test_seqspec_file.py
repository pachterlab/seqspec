from seqspec.seqspec_file import seqspec_file
from seqspec.Assay import Assay
from seqspec.File import File


def test_seqspec_file(dogmaseq_dig_spec: Assay):
    # Test with default parameters (selector='read')
    files = seqspec_file(spec=dogmaseq_dig_spec, modality="rna")
    assert "rna_R1" in files
    assert "rna_R2" in files
    assert isinstance(files["rna_R1"][0], File)

    # Check rna_R1 file content
    rna_r1_file = files["rna_R1"][0]
    assert rna_r1_file.file_id == "rna_R1_SRR18677638.fastq.gz"
    assert rna_r1_file.filename == "rna_R1_SRR18677638.fastq.gz"
    assert rna_r1_file.filetype == "fastq"
    assert rna_r1_file.filesize == 18499436
    assert (
        rna_r1_file.url
        == "fastqs/rna_R1_SRR18677638.fastq.gz"
    )
    assert rna_r1_file.urltype == "local"
    assert rna_r1_file.md5 == "7eb15a70da9b729b5a87e30b6596b641"

    # Test with ids
    files = seqspec_file(
        spec=dogmaseq_dig_spec, modality="rna", ids=["rna_R1"], selector="read"
    )
    assert "rna_R1" in files
    assert "rna_R2" not in files
    assert files["rna_R1"][0].filename == "rna_R1_SRR18677638.fastq.gz"


def test_list_files(dogmaseq_dig_spec: Assay):
    # Test list_read_files
    files = seqspec_file(spec=dogmaseq_dig_spec, modality="rna", selector="read")
    assert "rna_R1" in files
    assert "rna_R2" in files
    rna_r1_file = files["rna_R1"][0]
    assert rna_r1_file.file_id == "rna_R1_SRR18677638.fastq.gz"
    assert rna_r1_file.filename == "rna_R1_SRR18677638.fastq.gz"

    # Test list_region_files
    files = seqspec_file(spec=dogmaseq_dig_spec, modality="rna", selector="region")
    assert "rna_cell_bc" in files
    rna_cell_bc_file = files["rna_cell_bc"][0]
    assert rna_cell_bc_file.file_id == "RNA-737K-arc-v1.txt"
    assert rna_cell_bc_file.filename == "RNA-737K-arc-v1.txt"
    assert rna_cell_bc_file.filetype == "txt"
    assert rna_cell_bc_file.filesize == 2142553
    assert (
        rna_cell_bc_file.url
        == "https://github.com/pachterlab/qcbc/raw/main/tests/10xMOME/RNA-737K-arc-v1.txt.gz"
    )
    assert rna_cell_bc_file.urltype == "https"
    assert rna_cell_bc_file.md5 == "a88cd21e801ae6f9a7d9a48b67ccf693"

    # Test list_all_files
    files = seqspec_file(spec=dogmaseq_dig_spec, modality="rna", selector="file")
    assert "rna_R1" in files
    assert "rna_R2" in files
    assert "rna_cell_bc" in files


def test_list_files_by_id(dogmaseq_dig_spec: Assay):
    # Test list_files_by_read_id
    files = seqspec_file(
        spec=dogmaseq_dig_spec, modality="rna", ids=["rna_R1"], selector="read"
    )
    assert "rna_R1" in files
    assert "rna_R2" not in files
    rna_r1_file = files["rna_R1"][0]
    assert rna_r1_file.file_id == "rna_R1_SRR18677638.fastq.gz"

    # Test list_files_by_file_id
    files = seqspec_file(
        spec=dogmaseq_dig_spec,
        modality="rna",
        ids=["rna_R1_SRR18677638.fastq.gz"],
        selector="file",
    )
    assert "rna_R1" in files
    assert "rna_R2" not in files
    rna_r1_file = files["rna_R1"][0]
    assert rna_r1_file.file_id == "rna_R1_SRR18677638.fastq.gz"

    # Test list_files_by_region_id
    files = seqspec_file(
        spec=dogmaseq_dig_spec, modality="rna", ids=["rna_cell_bc"], selector="region"
    )
    assert "rna_cell_bc" in files
    assert "rna_umi" not in files
    rna_cell_bc_file = files["rna_cell_bc"][0]
    assert rna_cell_bc_file.file_id == "RNA-737K-arc-v1.txt"

    # Test list_files_by_region_type
    files = seqspec_file(
        spec=dogmaseq_dig_spec, modality="rna", ids=["barcode"], selector="region-type"
    )
    assert "rna_cell_bc" in files
    assert "rna_umi" not in files
    rna_cell_bc_file = files["rna_cell_bc"][0]
    assert rna_cell_bc_file.file_id == "RNA-737K-arc-v1.txt"

import pytest
from seqspec.File import File, FileInput, RustFile

def test_rustfile_roundtrip_and_mutation():
    # Skip if the Rust extension isn't built
    pytest.importorskip("seqspec._core")

    # Build a Pydantic File, wrap it in Rust, mutate in Rust, snapshot back
    fin = FileInput(filename="r1.fastq.gz")
    py = fin.to_file()
    rf = RustFile.from_model(py)

    # Properties reflect Rust state
    assert rf.file_id == py.file_id
    assert rf.filename == py.filename

    # Mutate in Rust
    rf.file_id = "new_id"
    snap = rf.snapshot()

    # Snapshot reflects Rust mutation; original Pydantic object is unchanged
    assert snap.file_id == "new_id"
    assert py.file_id != "new_id"


def test_rustfile_on_real_spec_file(dogmaseq_dig_spec):
    # Skip if the Rust extension isn't built
    pytest.importorskip("seqspec._core")

    # Take an existing File from the spec and round-trip through Rust
    rna_r1 = dogmaseq_dig_spec.sequence_spec[0].files[0]
    rf = RustFile.from_model(rna_r1)

    # Assert parity on all attributes
    assert rf.file_id == rna_r1.file_id
    assert rf.filename == rna_r1.filename
    assert rf.filetype == rna_r1.filetype
    assert rf.filesize == rna_r1.filesize
    assert rf.url == rna_r1.url
    assert rf.urltype == rna_r1.urltype
    assert rf.md5 == rna_r1.md5

    # Mutate in Rust and snapshot back
    new_id = rna_r1.file_id + ".tmp"
    rf.file_id = new_id
    snap = rf.snapshot()
    assert snap.file_id == new_id
    # Original spec object remains unchanged
    assert rna_r1.file_id != new_id
from seqspec.seqspec_modify import (
    seqspec_modify_read,
    seqspec_modify_region,
    seqspec_modify_files,
)
from seqspec.Assay import Assay


def test_seqspec_modify_read(temp_spec: Assay):
    modality = "rna"
    new_name = "renamed_rna_R1"
    new_read_data = [{"read_id": "rna_R1", "name": new_name}]
    spec = seqspec_modify_read(temp_spec, modality, new_read_data)
    read = spec.get_read("rna_R1")
    assert read.name == new_name


def test_seqspec_modify_region(temp_spec: Assay):
    modality = "rna"
    new_name = "renamed_rna_cell_bc"
    new_region_data = [{"region_id": "rna_cell_bc", "name": new_name}]
    spec = seqspec_modify_region(temp_spec, modality, new_region_data)
    region = spec.get_libspec(modality).get_region_by_id("rna_cell_bc")[0]
    assert region.name == new_name


def test_seqspec_modify_files(temp_spec: Assay):
    modality = "rna"
    new_url = "./fastq/R1.fastq.gz"
    new_file_data = [{"file_id": "rna_R1_SRR18677638.fastq.gz", "url": new_url}]
    spec = seqspec_modify_files(temp_spec, modality, new_file_data)
    file = spec.get_read("rna_R1").files[0]
    assert file.url == new_url

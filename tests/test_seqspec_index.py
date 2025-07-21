from seqspec.seqspec_index import seqspec_index, format_index
from seqspec.Assay import Assay
import json


def test_seqspec_index(dogmaseq_dig_spec: Assay):
    # Test get_index_by_read_ids
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="rna", ids=["rna_R1"], idtype="read"
    )
    assert len(indices) == 1
    assert "rna_R1" in indices[0]
    assert indices[0]["strand"] == "pos"

    # Test get_index_by_file_ids
    indices = seqspec_index(
        spec=dogmaseq_dig_spec,
        modality="rna",
        ids=["rna_R1_SRR18677638.fastq.gz"],
        idtype="file",
    )
    assert len(indices) == 1
    assert "rna_R1" in indices[0]

    # Test get_index_by_region_ids



def test_format_index(dogmaseq_dig_spec: Assay):
    # Test tab format
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="rna", ids=["rna_R1"], idtype="read"
    )
    formatted_index = format_index(indices, "tab")
    assert "rna_R1\tCell Barcode\tbarcode\t0\t16\nrna_R1\tumi\tumi\t16\t28" == formatted_index

    # Test kallisto bus format
    indices = seqspec_index(
        spec=dogmaseq_dig_spec, modality="rna", ids=["rna_R1", "rna_R2"], idtype="read"
    )
    print(indices)
    formatted_index = format_index(indices, "kb")
    assert "0,0,16:0,16,28:1,0,102" in formatted_index

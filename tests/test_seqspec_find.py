from seqspec.seqspec_find import seqspec_find
from seqspec.Assay import Assay
from seqspec.Region import Region
from seqspec.Read import Read
from seqspec.File import File


def test_seqspec_find(dogmaseq_dig_spec: Assay):
    # Test find_by_region_type
    regions = seqspec_find(
        spec=dogmaseq_dig_spec, selector="region-type", modality="rna", id="barcode"
    )
    assert len(regions) > 0
    assert all(isinstance(r, Region) for r in regions)
    assert all(r.region_type == "barcode" for r in regions if isinstance(r, Region))

    # Test find_by_region_id
    regions = seqspec_find(
        spec=dogmaseq_dig_spec, selector="region", modality="rna", id="rna_cell_bc"
    )
    assert len(regions) == 1
    assert isinstance(regions[0], Region)
    assert regions[0].region_id == "rna_cell_bc"

    # Test find_by_read_id
    reads = seqspec_find(
        spec=dogmaseq_dig_spec, selector="read", modality="rna", id="rna_R1"
    )
    assert len(reads) == 1
    assert isinstance(reads[0], Read)
    assert reads[0].read_id == "rna_R1"

    # Test find_by_file_id
    files = seqspec_find(
        spec=dogmaseq_dig_spec,
        selector="file",
        modality="rna",
        id="rna_R1_SRR18677638.fastq.gz",
    )
    assert len(files) == 1
    assert isinstance(files[0], File)
    assert files[0].file_id == "rna_R1_SRR18677638.fastq.gz"

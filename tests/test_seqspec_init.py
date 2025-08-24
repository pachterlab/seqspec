from seqspec.seqspec_init import seqspec_init
from seqspec.Assay import Assay
from seqspec.Region import Region


def test_seqspec_init():
    # Define test data
    name = "test_assay"
    doi = "10.1234/test.doi"
    date = "2023-01-01"
    description = "A test assay"
    modalities = ["rna", "atac"]

    # Call the function
    spec = seqspec_init(name, doi, date, description, modalities)

    # Assertions
    assert isinstance(spec, Assay)
    assert spec.name == name
    assert spec.doi == doi
    assert spec.date == date
    assert spec.description == description
    assert spec.modalities == modalities

    assert len(spec.library_spec) == len(modalities)
    for i, mod in enumerate(modalities):
        region = spec.library_spec[i]
        assert isinstance(region, Region)
        assert region.region_id == mod
        assert region.region_type == "meta"
        assert region.name == mod
        assert region.sequence_type == ""
        assert region.regions == []

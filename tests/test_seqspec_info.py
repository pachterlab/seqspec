from seqspec.seqspec_info import seqspec_info, format_info
from seqspec.Assay import Assay
import json


def test_seqspec_info(dogmaseq_dig_spec: Assay):
    # Test getting modalities
    info = seqspec_info(spec=dogmaseq_dig_spec, key="modalities")
    assert "modalities" in info
    assert set(info["modalities"]) == {"protein", "tag", "rna", "atac"}

    # Test getting meta
    info = seqspec_info(spec=dogmaseq_dig_spec, key="meta")
    assert "meta" in info
    assert info["meta"]["assay_id"] == "DOGMAseq-DIG"

    # Test getting sequence_spec
    info = seqspec_info(spec=dogmaseq_dig_spec, key="sequence_spec")
    assert "sequence_spec" in info
    assert len(info["sequence_spec"]) > 0

    # Test getting library_spec
    info = seqspec_info(spec=dogmaseq_dig_spec, key="library_spec")
    assert "library_spec" in info
    assert "rna" in info["library_spec"]


def test_format_info(dogmaseq_dig_spec: Assay):
    # Test formatting modalities
    info = seqspec_info(spec=dogmaseq_dig_spec, key="modalities")
    formatted_info = format_info(info, "modalities", "tab")
    assert "protein\ttag\trna\tatac" in formatted_info

    # Test formatting meta as json
    info = seqspec_info(spec=dogmaseq_dig_spec, key="meta")
    formatted_info = format_info(info, "meta", "json")
    meta_dict = json.loads(formatted_info)
    assert meta_dict["name"] == "DOGMAseq-DIG/Illumina"

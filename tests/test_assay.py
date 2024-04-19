import json
from unittest import TestCase
from seqspec.Region import Region
from seqspec.Assay import Assay

from seqspec import __version__

from .test_region import (
    region_rna_joined_dict,
    region_rna_umi_dict,
    region_rna_linker_dict,
)


def assay_dict(reads=[], regions=[]):
    return {
        "seqspec_version": __version__,
        "assay_id": "My assay",
        "name": "A machine-readable specification for genomics assays",
        "doi": "https://doi.org/10.1101/2023.03.17.533215",
        "date": "20230317",
        "description": "description",
        "modalities": ["RNA", "cDNA"],
        "lib_struct": "lib_struct",
        "sequence_protocol": "illumina protocol",
        "sequence_kit": "illumina kit",
        "library_protocol": "10x protocol",
        "library_kit": "10x v3 kit",
        "sequence_spec": reads,
        "library_spec": regions,
    }


class TestAssay(TestCase):
    def test_minimal(self):
        expected = assay_dict()

        a = Assay(**assay_dict())
        self.assertEqual(a.to_dict(), expected)

        self.assertEqual(a.to_JSON(), json.dumps(expected, sort_keys=False, indent=4))

    def test_assay_with_regions(self):
        r_umi_dict = region_rna_umi_dict("region-2")
        r_umi = Region(**r_umi_dict)
        r_linker_dict = region_rna_linker_dict("region-3")
        r_linker = Region(**r_linker_dict)
        r_expected_dict = region_rna_joined_dict("region-1", [r_umi, r_linker])
        r_expected = Region(**r_expected_dict)

        expected = assay_dict(reads=[], regions=[r_expected])

        a = Assay(**expected)

        self.assertEqual(a.get_libspec("RNA"), r_expected)

        self.assertRaises(IndexError, a.get_libspec, "cDNA")

    def test_assay_invalid_data(self):
        with self.assertRaises(TypeError):
            Assay(123)  # Passing a non-dict type should raise TypeError

        # Create a valid assay dictionary and add an unknown key to it
        invalid_assay_data = assay_dict()
        invalid_assay_data["unknown_key"] = "unknown_value"
        with self.assertRaises(TypeError):  # Expecting TypeError for unknown keys
            Assay(**invalid_assay_data)

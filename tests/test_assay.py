import json
from unittest import TestCase
from seqspec.Region import Region
from seqspec.Assay import Assay

from .test_region import (
    region_rna_joined_dict,
    region_rna_umi_dict,
    region_rna_linker_dict,
)


def assay_dict(regions=[]):
    return {
        "seqspec_version": "0.0.0",
        "assay": "My assay",
        "sequencer": "My sequencing machine",
        "name": "A machine-readable specification for genomics assays",
        "doi": "https://doi.org/10.1101/2023.03.17.533215",
        "publication_date": "20230317",
        "description": "description",
        "modalities": ["RNA", "cDNA"],
        "lib_struct": "lib_struct",
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

        expected = assay_dict(regions=[r_expected])

        a = Assay(**expected)

        self.assertEqual(a.get_libspec("RNA"), r_expected)

        self.assertRaises(IndexError, a.get_libspec, "cDNA")

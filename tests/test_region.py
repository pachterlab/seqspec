from unittest import TestCase

from seqspec.Read import Read
from seqspec.Region import (
    Onlist,
    Region,
    project_regions_to_coordinates,
)


def region_rna_joined_dict(region_id, regions=[]):
    expected = {
        "region_id": region_id,
        "region_type": "joined",
        "name": f"{region_id}-joined",
        "sequence_type": "RNA",
        "regions": regions,
    }
    return expected


def region_rna_umi_dict(region_id, regions=[]):
    expected = {
        "region_id": region_id,
        "region_type": "umi",
        "name": f"{region_id}-umi",
        "sequence_type": "RNA",
        "sequence": "NNNNNN",
        "regions": regions,
    }
    return expected


def region_rna_linker_dict(region_id, regions=[]):
    expected = {
        "region_id": region_id,
        "region_type": "linker",
        "name": f"{region_id}-linker",
        "sequence_type": "RNA",
        "sequence": "CATTGG",
        "regions": regions,
    }
    return expected


def read_rna_dict(read_id, min_len=0, max_len=100):
    expected = {
        "read_id": read_id,
        "name": f"{read_id}-name",
        "modality": "RNA",
        "primer_id": f"{read_id}-primer",
        "min_len": min_len,
        "max_len": max_len,
        "strand": "pos",
        "files": [],
    }
    return expected


class TestOnlist(TestCase):
    def test_simple_onlist(self):
        filename = "barcodes.tsv"
        expected = {
            "file_id": "123",
            "filename": filename,
            "filetype": "tsv",
            "filesize": 300,
            "url": filename,
            "urltype": "file",
            "md5": "d41d8cd98f00b204e9800998ecf8427e",
        }
        permit = Onlist(**expected)

        self.assertEqual(permit.dict(), expected)


class TestRegion(TestCase):
    def test_minimal_region(self):
        expected = region_rna_joined_dict("region-1")
        r = Region(**expected)
        self.assertEqual(r.region_id, expected["region_id"])
        self.assertEqual(r.region_type, expected["region_type"])
        self.assertEqual(r.name, expected["name"])
        self.assertEqual(r.sequence_type, expected["sequence_type"])
        self.assertEqual(r.sequence, "")
        self.assertEqual(r.min_len, 0)
        self.assertEqual(r.max_len, 1024)
        self.assertIs(r.onlist, None)
        self.assertEqual(r.regions, [])

        self.assertEqual(r.get_region_by_id(expected["region_id"]), [r])
        self.assertEqual(r.get_region_by_region_type(expected["region_type"]), [r])
        self.assertEqual(r.get_leaves(), [r])
        self.assertEqual(r.get_leaf_region_types(), set([expected["region_type"]]))

    def test_unique_subregions(self):
        r_umi_dict = region_rna_umi_dict("region-2")
        r_umi = Region(**r_umi_dict)
        r_linker_dict = region_rna_linker_dict("region-3")
        r_linker = Region(**r_linker_dict)
        r_expected_dict = region_rna_joined_dict("region-1", [r_umi, r_linker])
        r_expected_dict["sequence"] = r_umi_dict["sequence"] + r_linker_dict["sequence"]
        r_expected = Region(**r_expected_dict)

        self.assertEqual(r_umi.get_sequence(), r_umi_dict["sequence"])
        self.assertEqual(r_linker.get_sequence(), r_linker_dict["sequence"])

        self.assertEqual(r_expected.regions[0].get_sequence(), r_umi_dict["sequence"])
        self.assertEqual(
            r_expected.regions[1].get_sequence(), r_linker_dict["sequence"]
        )
        self.assertEqual(
            r_expected.get_sequence(),
            r_umi_dict["sequence"] + r_linker_dict["sequence"],
        )

        self.assertEqual(r_expected.get_region_by_id(r_umi_dict["region_id"]), [r_umi])
        self.assertEqual(
            r_expected.get_region_by_region_type(r_umi_dict["region_type"]), [r_umi]
        )
        self.assertEqual(
            r_expected.get_region_by_id(r_linker_dict["region_id"]), [r_linker]
        )
        self.assertEqual(
            r_expected.get_region_by_region_type(r_linker_dict["region_type"]),
            [r_linker],
        )
        self.assertEqual(r_expected.get_leaves(), [r_umi, r_linker])
        self.assertEqual(
            r_expected.get_leaf_region_types(),
            set([r_umi_dict["region_type"], r_linker_dict["region_type"]]),
        )

        # 0 & 1024 are the default min & max, it does not recurse to update the lengths
        self.assertEqual(r_expected.min_len, 0)
        self.assertEqual(r_expected.max_len, 1024)

        # update_attr searches through regions to sums up all the mins & maxes
        r_expected.update_attr()
        self.assertEqual(r_expected.min_len, 0)
        self.assertEqual(r_expected.max_len, 1024 * len(r_expected.get_leaves()))

    def test_retrieving_subregions_with_same_types(self):
        r2_dict = region_rna_umi_dict("region-2")
        r2 = Region(**r2_dict)
        r3_dict = region_rna_linker_dict("region-3")
        r3 = Region(**r3_dict)
        r4_dict = region_rna_umi_dict("region-4")
        r4 = Region(**r4_dict)
        r1_dict = region_rna_joined_dict("region-1", [r2, r3, r4])
        r1 = Region(**r1_dict)

        self.assertEqual(r1.get_region_by_region_type(r2_dict["region_type"]), [r2, r4])

    def test_set_parent_id(self):
        r2_dict = region_rna_umi_dict("region-2")
        r2 = Region(**r2_dict)
        r3_dict = region_rna_linker_dict("region-3")
        r3 = Region(**r3_dict)

        r5_dict = region_rna_umi_dict("region-5")
        r5 = Region(**r5_dict)
        r6_dict = region_rna_linker_dict("region-5")
        r6 = Region(**r6_dict)
        r4_dict = region_rna_joined_dict("region-4", [r5, r6])
        r4 = Region(**r4_dict)

        r1_regions = [r2, r3, r4]
        r1_dict = region_rna_joined_dict("region-1", r1_regions)
        r1 = Region(**r1_dict)

        self.assertEqual(len(r1.regions), len(r1_regions))

    def test_onlists(self):
        region_data = {
            "region_id": "region-id-1",
            "region_type": "linker",
            "name": "region-1",
            "sequence_type": "stuff",
            "sequence": "AACGTGAT",
            "min_len": 50,
            "max_len": 1024,
            "regions": None,
        }

        filename = "barcodes.tsv"
        onlist_data = {
            "file_id": "123",
            "filename": filename,
            "filetype": "tsv",
            "filesize": 300,
            "url": filename,
            "urltype": "file",
            "md5": "d41d8cd98f00b204e9800998ecf8427e",
        }

        permitted = Onlist(**onlist_data)

        r = Region(**region_data, onlist=permitted)

        expected = region_data.copy()
        expected["onlist"] = onlist_data

        self.assertEqual(r.dict(), expected)


class TestRegionCoordinates(TestCase):
    def test_project_regions_to_coordinates(self):
        r1_dict = region_rna_umi_dict("region-1")
        r1 = Region(**r1_dict)
        r2_dict = region_rna_linker_dict("region-2")
        r2 = Region(**r2_dict)

        r3_dict = region_rna_umi_dict("region-3")
        r3 = Region(**r3_dict)
        r4_dict = region_rna_linker_dict("region-4")
        r4 = Region(**r4_dict)

        regions = [r1, r2, r3, r4]
        coords = project_regions_to_coordinates(regions)

        cur_start = 0
        for r, c in zip(regions, coords):
            cur_stop = cur_start + r.max_len
            self.assertEqual(c.start, cur_start)
            self.assertEqual(c.stop, cur_stop)
            cur_start = cur_stop


class TestRead(TestCase):
    def test_minimal_read(self):
        expected = read_rna_dict("read-1")
        r = Read(**expected)
        for key in expected:
            self.assertEqual(getattr(r, key), expected[key])

        self.assertEqual(repr(r), repr(expected))
        self.assertEqual(r.to_dict(), expected)

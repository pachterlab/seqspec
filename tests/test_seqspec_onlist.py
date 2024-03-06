import os
from tempfile import TemporaryDirectory
from unittest import TestCase

from seqspec.Region import Onlist
from seqspec.seqspec_onlist import (
    find_list_target_dir,
    join_product_onlist,
    join_multi_onlist,
)


class TestSeqspecOnlist(TestCase):
    def test_find_list_target_dir_local(self):
        with TemporaryDirectory(prefix="onlist_tmp_") as tmpdir:
            filename = os.path.join(tmpdir, "temp.txt")
            
            onlist1 = Onlist(filename, "d41d8cd98f00b204e9800998ecf8427e", "local")

            target_dir = find_list_target_dir([onlist1])
            self.assertEqual(target_dir, tmpdir)

    def test_find_list_target_dir_remote(self):
        onlist1 = Onlist("http:localhost:9/temp.txt", "d41d8cd98f00b204e9800998ecf8427e", "remote")

        target_dir = find_list_target_dir([onlist1])
        self.assertEqual(target_dir, os.getcwd())
        
    def test_join_product_onlist(self):
        onlists = [
            ["AAAA", "TTTT"],
            ["GGGG", "CCCC"],
        ]

        joined = list(join_product_onlist(onlists))
        self.assertEqual(len(joined), 4)
        self.assertEqual(joined[0], "AAAAGGGG\n")
        self.assertEqual(joined[3], "TTTTCCCC\n")

    def test_join_multi_onlist(self):
        onlists = [
            ["AAAA", "TTTT"],
            ["GGGG", "CCCC", "GGTT"],
        ]

        joined = list(join_multi_onlist(onlists))
        self.assertEqual(len(joined), 3)
        self.assertEqual(joined[0], "AAAA GGGG\n")
        self.assertEqual(joined[1], "TTTT CCCC\n")
        self.assertEqual(joined[2], "- GGTT\n")


from contextlib import contextmanager
from io import StringIO
import os
from tempfile import TemporaryDirectory
from unittest import TestCase

from seqspec.Region import Onlist
from seqspec.seqspec_onlist import (
    find_list_target_dir,
    join_onlists,
    join_product_onlist,
    join_multi_onlist,
    join_onlists,
    run_onlist_region,
    run_onlist_read,
)
from .test_utils import example_spec, load_example_spec


@contextmanager
def create_temporary_barcode_files(filenames):
    if isinstance(filenames, str):
        filenames = [filenames]

    cwd = os.getcwd()
    try:
        with TemporaryDirectory(prefix="test_onlist_") as tmpdir:
            os.chdir(tmpdir)
            for name in filenames:
                filename = os.path.join(tmpdir, name)
                with open(filename, "wt") as outstream:
                    pass
            yield tmpdir
    finally:
        os.chdir(cwd)


class TestSeqspecOnlist(TestCase):
    def test_run_onlist_region(self):
        with create_temporary_barcode_files(["index_onlist.txt"]):
            spec = load_example_spec(example_spec)
            # returns the one local barcode path
            regions = run_onlist_region(spec, "rna", "index")
            self.assertEqual(len(regions), 1)
            region = regions[0]
            self.assertEqual(region.location, "local")
            self.assertEqual(region.filename, "index_onlist.txt")
            self.assertEqual(region.md5, "939cb244b4c43248fcc795bbe79599b0")

    def test_run_onlist_read(self):
        with create_temporary_barcode_files(["index_onlist.txt"]):
            spec = load_example_spec(example_spec)
            reads = run_onlist_read(spec, "rna", "read2.fastq.gz")
            self.assertEqual(len(reads), 1)
            read = reads[0]
            self.assertEqual(read.location, "local")
            self.assertEqual(read.filename, "index_onlist.txt")
            self.assertEqual(read.md5, "939cb244b4c43248fcc795bbe79599b0")

    def test_find_list_target_dir_local(self):
        with create_temporary_barcode_files(["index_onlist.txt"]) as tmpdir:
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

    def test_join_onlist_product(self):
        onlists = [
            ["AAAA", "TTTT"],
            ["GGGG", "CCCC"],
        ]

        joined = list(join_onlists(onlists, "product"))
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

    def test_join_onlist_multi(self):
        onlists = [
            ["AAAA", "TTTT"],
            ["GGGG", "CCCC", "GGTT"],
        ]

        joined = list(join_onlists(onlists, "multi"))
        self.assertEqual(len(joined), 3)
        self.assertEqual(joined[0], "AAAA GGGG\n")
        self.assertEqual(joined[1], "TTTT CCCC\n")
        self.assertEqual(joined[2], "- GGTT\n")

from argparse import ArgumentParser
from contextlib import contextmanager
from io import StringIO
import os
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from seqspec.Region import Onlist
from seqspec.seqspec_onlist import (
    find_list_target_dir,
    join_onlists,
    join_product_onlist,
    join_multi_onlist,
    join_onlists,
    run_onlist_region,
    run_onlist_read,
    setup_onlist_args,
    validate_onlist_args,
    write_onlist,
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
        self.assertEqual(joined[0], "AAAAGGGG")
        self.assertEqual(joined[3], "TTTTCCCC")

    def test_join_onlist_product(self):
        onlists = [
            ["AAAA", "TTTT"],
            ["GGGG", "CCCC"],
        ]

        joined = list(join_onlists(onlists, "product"))
        self.assertEqual(len(joined), 4)
        self.assertEqual(joined[0], "AAAAGGGG")
        self.assertEqual(joined[3], "TTTTCCCC")

    def test_join_multi_onlist(self):
        onlists = [
            ["AAAA", "TTTT"],
            ["GGGG", "CCCC", "GGTT"],
        ]

        joined = list(join_multi_onlist(onlists))
        self.assertEqual(len(joined), 3)
        self.assertEqual(joined[0], "AAAA GGGG")
        self.assertEqual(joined[1], "TTTT CCCC")
        self.assertEqual(joined[2], "- GGTT")

    def test_join_onlist_multi(self):
        onlists = [
            ["AAAA", "TTTT"],
            ["GGGG", "CCCC", "GGTT"],
        ]

        joined = list(join_onlists(onlists, "multi"))
        self.assertEqual(len(joined), 3)
        self.assertEqual(joined[0], "AAAA GGGG")
        self.assertEqual(joined[1], "TTTT CCCC")
        self.assertEqual(joined[2], "- GGTT")

    def test_local_validate_onlist_args(self):
        onlist_name = "index_onlist.txt"
        with create_temporary_barcode_files([onlist_name]) as tmpdir:
            expected_onlist_path = os.path.join(tmpdir, onlist_name)
            spec_path = os.path.join(tmpdir, "spec.yaml")

            parser = ArgumentParser()
            subparser = parser.add_subparsers(dest="command")
            subparser = setup_onlist_args(subparser)
            args = parser.parse_args([
                "onlist", "-m", "rna", "-r", "read1.fastq.gz", "-f", "multi", spec_path])

            def load_spec(*args, **kwargs):
                return load_example_spec(example_spec)

            with patch("seqspec.seqspec_onlist.load_spec", load_spec) as loader:
                onlist_path = validate_onlist_args(parser, args)

                self.assertEqual(onlist_path, expected_onlist_path)

    def test_local_cached_remote_validate_onlist_args(self):
        # Test that we will can use a locally cached copy of one barcode file
        # even if it is marked remote.
        onlist_name = "index_onlist.txt"
        with create_temporary_barcode_files([onlist_name]) as tmpdir:
            expected_onlist_path = os.path.join(tmpdir, onlist_name)
            spec_path = os.path.join(tmpdir, "spec.yaml")

            parser = ArgumentParser()
            subparser = parser.add_subparsers(dest="command")
            subparser = setup_onlist_args(subparser)
            args = parser.parse_args([
                "onlist", "-m", "rna", "-r", "read1.fastq.gz", "-f", "multi", spec_path])

            def load_spec(*args, **kwargs):
                remote_spec = example_spec.replace(
                    "location: local",
                    "location: remote"
                ).replace(
                    "filename: index_onlist.txt",
                    "filename: http://localhost:9/foo/index_onlist.txt"
                )
                print(remote_spec)
                return load_example_spec(remote_spec)

            with patch("seqspec.seqspec_onlist.load_spec", load_spec) as loader:
                onlist_path = validate_onlist_args(parser, args)

                self.assertEqual(onlist_path, expected_onlist_path)

    def test_write_onlist_no_double_spacing(self):
        # Make sure that joined onlists don't end up double spaced.
        
        onlists = [
            ["AAAA", "TTTT"],
            ["GGGG", "CCCC", "GGTT"],
        ]
        joined = list(join_multi_onlist(onlists))

        with TemporaryDirectory(prefix="seqspec_test_") as tmpdir:
            target = os.path.join(tmpdir, "onlist_joined.txt")
            write_onlist(joined, target)

            with open(target, "rt") as instream:
                saved = []
                for line in instream:
                    saved.append(line.rstrip())

        assert len(saved) == 3
        assert saved == joined

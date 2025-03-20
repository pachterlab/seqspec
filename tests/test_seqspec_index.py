from argparse import ArgumentParser
from contextlib import contextmanager
from importlib import resources
from io import StringIO
import os
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from seqspec.seqspec_index import (
    setup_index_args,
    validate_index_args,
)
from .test_utils import example_spec, load_example_spec


class TestSeqspecIndex(TestCase):
    def test_index_kb_with_fastq_gz(self):
        parser = ArgumentParser()
        subparser = parser.add_subparsers(dest="command")
        subparser = setup_index_args(subparser)
        with resources.path("tests.data", "IGVFFI5228SMZU_fastq_gz.yaml") as spec_path:
            args = parser.parse_args([
                "index",
                "-m",
                "rna",
                "-t",
                "kb",
                "-s",
                "read",
                "-i",
                "IGVFFI0800JAPD.fastq.gz,IGVFFI5241MPKQ.fastq.gz",
                str(spec_path)])

        kb_tool = validate_index_args(parser, args)
        self.assertEqual(kb_tool, "1,10,18,1,48,56,1,78,86:1,0,10:0,0,140")

    def test_index_kb_without_fastq_gz(self):
        parser = ArgumentParser()
        subparser = parser.add_subparsers(dest="command")
        subparser = setup_index_args(subparser)
        with resources.path("tests.data", "IGVFFI5228SMZU.yaml") as spec_path:
            args = parser.parse_args([
                "index",
                "-m",
                "rna",
                "-t",
                "kb",
                "-s",
                "read",
                "-i",
                "IGVFFI0800JAPD,IGVFFI5241MPKQ",
                str(spec_path)])

        kb_tool = validate_index_args(parser, args)
        self.assertEqual(kb_tool, "1,10,18,1,48,56,1,78,86:1,0,10:0,0,140")

    def test_index_chromap_with_fastq_gz(self):
        parser = ArgumentParser()
        subparser = parser.add_subparsers(dest="command")
        subparser = setup_index_args(subparser)
        with resources.path("tests.data", "IGVFFI9241RRZV_fastq_gz.yaml") as spec_path:
            args = parser.parse_args([
                "index",
                "-m",
                "atac",
                "-t",
                "chromap",
                "-s",
                "read",
                "-i",
                "IGVFFI4653IBZO.fastq.gz,IGVFFI3278EOPV.fastq.gz",
                str(spec_path)])

        chromap_tool = validate_index_args(parser, args)
        self.assertEqual(
            chromap_tool,
            "-1 IGVFFI4653IBZO.fastq.gz -2 IGVFFI3278EOPV.fastq.gz --barcode IGVFFI3278EOPV.fastq.gz --read-format bc:65:72,bc:103:110,bc:141:148,r1:0:149,r2:0:49")

        
    def test_index_chromap_without_fastq_gz(self):
        parser = ArgumentParser()
        subparser = parser.add_subparsers(dest="command")
        subparser = setup_index_args(subparser)
        with resources.path("tests.data", "IGVFFI9241RRZV.yaml") as spec_path:
            args = parser.parse_args([
                "index",
                "-m",
                "atac",
                "-t",
                "chromap",
                "-s",
                "read",
                "-i",
                "IGVFFI4653IBZO,IGVFFI3278EOPV",
                str(spec_path)])

        chromap_tool = validate_index_args(parser, args)
        self.assertEqual(
            chromap_tool,
            "-1 IGVFFI4653IBZO.fastq.gz -2 IGVFFI3278EOPV.fastq.gz --barcode IGVFFI3278EOPV.fastq.gz --read-format bc:65:72,bc:103:110,bc:141:148,r1:0:149,r2:0:49")

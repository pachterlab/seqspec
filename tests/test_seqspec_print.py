from argparse import ArgumentParser
from io import StringIO
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.mock import patch

from matplotlib.figure import Figure

from seqspec.seqspec_print import (
    run_print_tree,
    run_print_png,
)
from seqspec.utils import (
    load_spec_stream
)

from .test_utils import example_spec as example_spec_text


class TestSeqspecPrint(TestCase):
    def setUp(self):
        self.example_spec  = load_spec_stream(StringIO(example_spec_text))

    def test_seqspec_print_tree(self):
        tree = run_print_tree(self.example_spec)
        self.assertIn("SOLiD_P1_adapter", tree)

    def test_seqspec_print_png(self):
        fig = run_print_png(self.example_spec)

        self.assertIsInstance(fig, Figure)

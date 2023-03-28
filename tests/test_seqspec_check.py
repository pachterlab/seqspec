from argparse import ArgumentParser
import os
from pathlib import Path
from unittest import TestCase, skipUnless

from seqspec.seqspec_check import (
    setup_check_args,
    validate_check_args,
)


test_dir = Path(__file__).parent
default_assay_dir = test_dir / '..' / 'assays'
assay_dir = os.environ.get("SEQSPEC_ASSAY_DIR", default_assay_dir)


def create_stub_check_parser():
    parser = ArgumentParser()
    subparser = parser.add_subparsers(
        dest="command",
        metavar="<CMD>",
    )
    subparser = setup_check_args(subparser)
    return parser


class TestSeqspecCheck(TestCase):
    def test_check_args(self):
        parser = create_stub_check_parser()

        output_name = "output"
        spec_name = "spec.yaml"
        cmdline = ["check", "-o", output_name, spec_name]
        args = parser.parse_args(cmdline)

        self.assertEqual(args.o, output_name)
        self.assertEqual(args.yaml, spec_name)

    @skipUnless(assay_dir.is_dir(), "Couldn't find assays directory")
    def test_validate_check_args(self):
        parser = create_stub_check_parser()

        spec = assay_dir / "Quartz-seq" / "spec.yaml"
        cmdline = ["check", str(spec)]
        args = parser.parse_args(cmdline)

        errors = validate_check_args(None, args)
        self.assertEqual(errors, 0)

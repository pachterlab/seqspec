from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from seqspec.seqspec_check import (
    setup_check_args,
    validate_check_args,
)

from .test_utils import example_spec


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

    def test_validate_check_args(self):
        parser = create_stub_check_parser()

        with TemporaryDirectory(prefix="seqspec_check_") as tmpdir:
            target = Path(tmpdir) / "spec.yaml"

            with open(target, "wt") as stream:
                stream.write(example_spec)

            cmdline = ["check", str(target)]
            args = parser.parse_args(cmdline)

            # ignore testing if the files barcode & fastq files exist
            with patch("os.path.exists") as path_exists:
                path_exists.return_value = True
                errors = validate_check_args(None, args)
                self.assertEqual(errors, [])

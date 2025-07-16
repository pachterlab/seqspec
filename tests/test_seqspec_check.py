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

        self.assertEqual(str(args.output), output_name)
        self.assertEqual(str(args.yaml), spec_name)

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
                self.assertEqual(errors, None)

    def test_check_with_igvf_skip(self):
        """Test that 'igvf' skip condition filters out some IGVF-related errors but not read_id pattern errors."""
        from seqspec.seqspec_check import run_check
        from argparse import ArgumentParser, Namespace

        # Create a parser
        parser = ArgumentParser()
        subparser = parser.add_subparsers(dest="command")
        subparser = setup_check_args(subparser)

        # Test file path
        test_file = Path("tests/data/seqspec_valid_ignore_onlist.yaml")

        # Test with 'igvf' skip
        args = Namespace()
        args.yaml = test_file
        args.output = None
        args.skip = "igvf"

        # Run check with igvf
        errors = run_check(parser, args)

        # Should have exactly 2 errors: read_id pattern error and onlist file error
        self.assertEqual(
            len(errors), 2, f"Expected 2 errors, got {len(errors)}: {errors}"
        )

        # Check for read_id pattern error (should not be filtered by igvf skip)
        read_id_errors = [
            e
            for e in errors
            if e.get("error_type") == "check_schema"
            and "read_id" in e.get("error_message", "")
        ]
        self.assertEqual(
            len(read_id_errors),
            1,
            f"Expected 1 read_id error, got {len(read_id_errors)}",
        )
        self.assertIn("1165AJSO", read_id_errors[0]["error_message"])
        self.assertIn("does not match", read_id_errors[0]["error_message"])

        # Check for onlist file error (should not be filtered by igvf skip)
        onlist_errors = [
            e for e in errors if e.get("error_type") == "check_onlist_files_exist"
        ]
        self.assertEqual(
            len(onlist_errors), 1, f"Expected 1 onlist error, got {len(onlist_errors)}"
        )
        self.assertIn("does not exist", onlist_errors[0]["error_message"])

    def test_check_with_igvf_onlist_skip(self):
        """Test that 'igvf_onlist_skip' skip condition filters out IGVF and onlist errors including read_id pattern."""
        from seqspec.seqspec_check import run_check
        from argparse import ArgumentParser, Namespace

        # Create a parser
        parser = ArgumentParser()
        subparser = parser.add_subparsers(dest="command")
        subparser = setup_check_args(subparser)

        # Test file path
        test_file = Path("tests/data/seqspec_valid_ignore_onlist.yaml")

        # Test with 'igvf_onlist_skip' skip
        args = Namespace()
        args.yaml = test_file
        args.output = None
        args.skip = "igvf_onlist_skip"

        # Run check with igvf_onlist_skip
        errors = run_check(parser, args)

        # Should have no errors (all errors are filtered out by igvf_onlist_skip)
        self.assertEqual(
            len(errors), 0, f"Expected 0 errors, got {len(errors)}: {errors}"
        )

    def test_check_without_skip(self):
        """Test that without skip condition, validation errors are reported."""
        from seqspec.seqspec_check import run_check
        from argparse import ArgumentParser, Namespace

        # Create a parser
        parser = ArgumentParser()
        subparser = parser.add_subparsers(dest="command")
        subparser = setup_check_args(subparser)

        # Test file path
        test_file = Path("tests/data/seqspec_valid_ignore_onlist.yaml")

        # Test without skip
        args = Namespace()
        args.yaml = test_file
        args.output = None
        args.skip = None

        # Run check without skip
        errors = run_check(parser, args)

        # Should have exactly 2 errors: sequence_protocol error and onlist file error
        self.assertEqual(
            len(errors), 2, f"Expected 2 errors, got {len(errors)}: {errors}"
        )

        # Check for sequence_protocol error
        protocol_errors = [
            e
            for e in errors
            if e.get("error_type") == "check_schema"
            and "sequence_protocol" in e.get("error_message", "")
        ]
        self.assertEqual(
            len(protocol_errors),
            1,
            f"Expected 1 sequence_protocol error, got {len(protocol_errors)}",
        )

        # Check for onlist file error
        onlist_errors = [
            e for e in errors if e.get("error_type") == "check_onlist_files_exist"
        ]
        self.assertEqual(
            len(onlist_errors), 1, f"Expected 1 onlist error, got {len(onlist_errors)}"
        )

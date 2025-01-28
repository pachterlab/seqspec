from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from seqspec.seqspec_check import (
    check,
    setup_check_args,
    validate_check_args,
)
from seqspec.utils import load_spec
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
                self.assertEqual(errors, None)

    def test_check_for_igvf_valid(self):
        spec_fn = "tests/data/seqspec_valid_igvf.yaml"
        spec = load_spec(spec_fn)
        errors = check(spec, spec_fn, for_igvf=True)
        self.assertEqual(errors, [])

    def test_check_invalid(self):
        expected_errors = [
            "[error 1] None is not of type 'string' in spec['lib_struct']",
            "[error 2] 'single-nucleus ATAC-seq' is not valid under any of the given schemas in spec['library_protocol']",
            "[error 3] {'kit_id': '10x-ATAC-RNA-MULTI'} is not valid under any of the given schemas in spec['library_kit']",
            "[error 4] 'Illumina' is not valid under any of the given schemas in spec['sequence_protocol']",
            "[error 5] 'NovaSeq X Series 10B Reagent' is not valid under any of the given schemas in spec['sequence_kit']",
            "[error 6] 1 is not of type 'string' in spec['sequence_spec'][0]['files'][0]['md5']",
            "[error 7] 1 is not of type 'string' in spec['library_spec'][0]['regions'][6]['onlist']['md5']",
        ]
        spec_fn = "tests/data/seqspec_valid_igvf.yaml"
        spec = load_spec(spec_fn)
        errors = check(spec, spec_fn)
        self.assertEqual(errors, expected_errors)

    def test_check_for_igvf_invalid(self):
        expected_errors = [
            "[error 1] 'atac-illumina_p5' max_len is less than min_len",
            "[error 2] 'atac-illumina_p5' sequence 'AATGATACGGCGACCACCGAGATCTACAC' has length 29, expected range (50, 29)",
        ]
        spec_fn = "tests/data/seqspec_invalid_igvf.yaml"
        spec = load_spec(spec_fn)
        errors = check(spec, spec_fn, for_igvf=True)
        self.assertEqual(errors, expected_errors)

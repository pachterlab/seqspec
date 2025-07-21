import os
import tempfile
from argparse import ArgumentParser
from pathlib import Path
from unittest import TestCase

import pytest

from seqspec.seqspec_check import (
    setup_check_args,
    validate_check_args,
)


def create_stub_check_parser():
    parser = ArgumentParser()
    subparser = parser.add_subparsers(
        dest="command",
        metavar="<CMD>",
    )
    subparser = setup_check_args(subparser)
    return parser



def test_check_args():
    """Test check command argument parsing."""
    parser = ArgumentParser()
    subparser = parser.add_subparsers()
    check_parser = setup_check_args(subparser)
    
    # Test with valid arguments
    args = check_parser.parse_args(['test.yaml'])
    assert args.yaml == Path('test.yaml')
    assert args.output is None
    assert args.skip is None
    
    # Test with output argument
    args = check_parser.parse_args(['test.yaml', '-o', 'output.txt'])
    assert args.yaml == Path('test.yaml')
    assert args.output == Path('output.txt')
    
    # Test with skip argument
    args = check_parser.parse_args(['test.yaml', '-s', 'igvf'])
    assert args.yaml == Path('test.yaml')
    assert args.skip == 'igvf'

def test_validate_check_args():
    """Test check command argument validation."""
    parser = ArgumentParser()
    subparser = parser.add_subparsers()
    check_parser = setup_check_args(subparser)
    
    # Test with valid file
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
        f.write(b'assay_id: test')
        f.flush()
        
        args = check_parser.parse_args([f.name])
        validate_check_args(parser, args)  # Should not raise
        
        os.unlink(f.name)
    
    # Test with non-existent file
    args = check_parser.parse_args(['nonexistent.yaml'])
    with pytest.raises(SystemExit):
        validate_check_args(parser, args)

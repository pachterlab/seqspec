"""Main module for seqspec CLI.

This module provides the main entry point for the seqspec command-line interface.
It handles argument parsing, command routing, and execution of subcommands.
"""

import sys
import warnings
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from typing import Any, Callable, Dict

from . import __version__
from .seqspec_check import run_check, setup_check_args
from .seqspec_file import run_file, setup_file_args
from .seqspec_find import run_find, setup_find_args
from .seqspec_format import run_format, setup_format_args
from .seqspec_index import run_index, setup_index_args
from .seqspec_info import run_info, setup_info_args
from .seqspec_init import run_init, setup_init_args
from .seqspec_insert import run_insert, setup_insert_args
from .seqspec_methods import run_methods, setup_methods_args
from .seqspec_modify import run_modify, setup_modify_args
from .seqspec_onlist import run_onlist, setup_onlist_args
from .seqspec_print import run_print, setup_print_args
from .seqspec_split import run_split, setup_split_args
from .seqspec_upgrade import run_upgrade, setup_upgrade_args
from .seqspec_version import run_version, setup_version_args


def setup_parser():
    """Create and configure the main argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = ArgumentParser(
        description=f"""
seqspec {__version__}: A machine-readable file format for genomic library sequence and structure.

GitHub: https://github.com/pachterlab/seqspec
Documentation: https://pachterlab.github.io/seqspec/
""",
        formatter_class=RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        metavar="<CMD>",
    )

    # Setup the arguments for all subcommands
    command_to_parser = {
        "check": setup_check_args(subparsers),
        "find": setup_find_args(subparsers),
        "file": setup_file_args(subparsers),
        "format": setup_format_args(subparsers),
        # "convert": setup_convert_args(subparsers),
        "index": setup_index_args(subparsers),
        "info": setup_info_args(subparsers),
        "init": setup_init_args(subparsers),
        "insert": setup_insert_args(subparsers),
        "methods": setup_methods_args(subparsers),
        "modify": setup_modify_args(subparsers),
        "onlist": setup_onlist_args(subparsers),
        "print": setup_print_args(subparsers),
        "split": setup_split_args(subparsers),
        "upgrade": setup_upgrade_args(subparsers),
        "version": setup_version_args(subparsers),
    }

    return parser, command_to_parser


def handle_no_args(
    parser: ArgumentParser, command_to_parser: Dict[str, ArgumentParser]
) -> None:
    """Handle case when no arguments are provided.

    Args:
        parser: Main argument parser.
        command_to_parser: Dictionary mapping commands to their parsers.
    """
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    if len(sys.argv) == 2:
        if sys.argv[1] in command_to_parser:
            command_to_parser[sys.argv[1]].print_help(sys.stderr)
        elif sys.argv[1] == "--version":
            print(f"seqspec {__version__}")
        else:
            parser.print_help(sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point for the seqspec CLI."""
    warnings.simplefilter("default", DeprecationWarning)

    parser, command_to_parser = setup_parser()
    handle_no_args(parser, command_to_parser)

    args = parser.parse_args()

    # Setup validator and runner for all subcommands
    command_to_function: Dict[str, Callable[[ArgumentParser, Namespace], Any]] = {
        "format": run_format,
        "print": run_print,
        "check": run_check,
        "find": run_find,
        "index": run_index,
        "info": run_info,
        "init": run_init,
        "methods": run_methods,
        "modify": run_modify,
        "onlist": run_onlist,
        "split": run_split,
        "version": run_version,
        "file": run_file,
        "upgrade": run_upgrade,
        # "convert": run_convert,
        "insert": run_insert,
    }

    try:
        command_to_function[sys.argv[1]](parser, args)
    except KeyError:
        parser.print_help(sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

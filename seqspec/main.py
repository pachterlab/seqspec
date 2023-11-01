from . import __version__
import argparse
import sys
from .seqspec_format import setup_format_args, validate_format_args
from .seqspec_print import setup_print_args, validate_print_args
from .seqspec_check import setup_check_args, validate_check_args
from .seqspec_find import setup_find_args, validate_find_args

# from .seqspec_convert import setup_convert_args, validate_convert_args
from .seqspec_modify import setup_modify_args, validate_modify_args
from .seqspec_index import setup_index_args, validate_index_args
from .seqspec_info import setup_info_args, validate_info_args

from .seqspec_split import setup_split_args, validate_split_args
from .seqspec_init import setup_init_args, validate_init_args
from .seqspec_onlist import setup_onlist_args, validate_onlist_args
from .seqspec_version import setup_version_args, validate_version_args

# Steps to add new subcommands
# Create seqspec_subcommand.py (create setup_subcmd_args, validate_subcmd_args, run_subcmd in that file)
# (in this file) from seqspec_subcmd import setup_subcmd_args, validate_subcmd_args
# Add setup_subcmd_args to command_to_parser along with its key==str(subcmd)
# Add validate_subcmd_args to COMMAND_TO_FUNCTION along with its key==str(subcmd)


def main():
    # setup parsers
    parser = argparse.ArgumentParser(
        description=f"seqspec {__version__}: Format sequence specification files"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        metavar="<CMD>",
    )

    # Setup the arguments for all subcommands
    command_to_parser = {
        "check": setup_check_args(subparsers),
        "find": setup_find_args(subparsers),
        "format": setup_format_args(subparsers),
        "index": setup_index_args(subparsers),
        "info": setup_info_args(subparsers),
        "init": setup_init_args(subparsers),
        "modify": setup_modify_args(subparsers),
        "onlist": setup_onlist_args(subparsers),
        "print": setup_print_args(subparsers),
        "split": setup_split_args(subparsers),
        "version": setup_version_args(subparsers),
    }
    # Show help when no arguments are given
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

    args = parser.parse_args()

    # Setup validator and runner for all subcommands (validate and run if valid)
    COMMAND_TO_FUNCTION = {
        "format": validate_format_args,
        "print": validate_print_args,
        "check": validate_check_args,
        "find": validate_find_args,
        "index": validate_index_args,
        "info": validate_info_args,
        "init": validate_init_args,
        "modify": validate_modify_args,
        "onlist": validate_onlist_args,
        "split": validate_split_args,
        "version": validate_version_args,
    }
    COMMAND_TO_FUNCTION[sys.argv[1]](parser, args)


if __name__ == "__main__":
    main()

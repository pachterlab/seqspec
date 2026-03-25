"""Main module for seqspec CLI.

This module provides the main entry point for the seqspec command-line interface.
It handles argument parsing, command routing, and execution of subcommands.
"""

import importlib
import logging
import sys
import warnings
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from typing import Any, Callable, Dict, Tuple

from . import __version__

COMMAND_MODULES: Dict[str, Tuple[str, str, str]] = {
    "auth": ("seqspec_auth", "setup_auth_args", "run_auth"),
    "check": ("seqspec_check", "setup_check_args", "run_check"),
    "file": ("seqspec_file", "setup_file_args", "run_file"),
    "find": ("seqspec_find", "setup_find_args", "run_find"),
    "format": ("seqspec_format", "setup_format_args", "run_format"),
    "index": ("seqspec_index", "setup_index_args", "run_index"),
    "info": ("seqspec_info", "setup_info_args", "run_info"),
    "init": ("seqspec_init", "setup_init_args", "run_init"),
    "insert": ("seqspec_insert", "setup_insert_args", "run_insert"),
    "methods": ("seqspec_methods", "setup_methods_args", "run_methods"),
    "modify": ("seqspec_modify", "setup_modify_args", "run_modify"),
    "onlist": ("seqspec_onlist", "setup_onlist_args", "run_onlist"),
    "print": ("seqspec_print", "setup_print_args", "run_print"),
    "split": ("seqspec_split", "setup_split_args", "run_split"),
    "upgrade": ("seqspec_upgrade", "setup_upgrade_args", "run_upgrade"),
    "version": ("seqspec_version", "setup_version_args", "run_version"),
}


def load_command(command: str) -> Tuple[Callable, Callable]:
    if command == "build":
        return setup_build_args, run_build

    module_name, setup_name, run_name = COMMAND_MODULES[command]
    module = importlib.import_module(f".{module_name}", __package__)
    return getattr(module, setup_name), getattr(module, run_name)


def setup_build_args(parser) -> ArgumentParser:
    subparser = parser.add_parser(
        "build",
        description="""
The LLM-backed build command is deprecated and will be removed.
---
""",
        help="Deprecated. This command will be removed.",
        formatter_class=RawTextHelpFormatter,
    )
    return subparser


def run_build(_: ArgumentParser, __: Namespace) -> None:
    raise RuntimeError(
        "seqspec build is deprecated. Use seqspec init/insert/modify or construct the spec directly."
    )


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
    parser.add_argument("--version", action="version", version=f"seqspec {__version__}")

    subparsers = parser.add_subparsers(
        dest="command",
        metavar="<CMD>",
    )

    # Setup the arguments for all subcommands
    command_to_parser = {}
    for command in ["auth", "build", *COMMAND_MODULES.keys()]:
        if command in command_to_parser:
            continue
        setup_func, _ = load_command(command)
        command_to_parser[command] = setup_func(subparsers)

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
        else:
            parser.print_help(sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point for the seqspec CLI."""
    warnings.simplefilter("default", DeprecationWarning)

    if len(sys.argv) == 2 and sys.argv[1] == "--version":
        print(f"seqspec {__version__}")
        sys.exit(0)
    if len(sys.argv) >= 2 and sys.argv[1] == "build":
        print(
            "seqspec build is deprecated. Use seqspec init/insert/modify or construct the spec directly.",
            file=sys.stderr,
        )
        sys.exit(1)

    logging.basicConfig(
        stream=sys.stderr,
        format="[%(levelname)s] %(message)s",
    )

    parser, command_to_parser = setup_parser()
    handle_no_args(parser, command_to_parser)

    args = parser.parse_args()

    # Setup validator and runner for all subcommands
    command_to_function: Dict[str, Callable[[ArgumentParser, Namespace], Any]] = {}
    for command in command_to_parser:
        _, run_func = load_command(command)
        command_to_function[command] = run_func

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

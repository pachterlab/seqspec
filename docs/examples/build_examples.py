"""Build or validate the examples docs tree."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from seqspec.examples_docs import build_examples_tree, validate_examples_tree


def main() -> int:
    """Run the examples build or validation command."""
    parser = argparse.ArgumentParser(
        description="Build or validate docs/examples for seqspec."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the current docs/examples tree instead of rebuilding it.",
    )
    args = parser.parse_args()

    if args.check:
        errors = validate_examples_tree()
        if errors:
            for error in errors:
                print(error)
            return 1
        print("docs/examples is valid")
        return 0

    build_examples_tree()
    print("rebuilt docs/examples")
    return 0


if __name__ == "__main__":
    sys.exit(main())

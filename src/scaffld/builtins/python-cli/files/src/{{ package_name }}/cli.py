"""Command-line interface for {{ project_name }}."""

from __future__ import annotations

import argparse
from typing import Optional, Sequence

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="{{ project_slug }}",
        description="{{ description | py }}",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("name", nargs="?", default="world", help="who to greet")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point. Returns a process exit code."""
    args = build_parser().parse_args(argv)
    print(f"Hello, {args.name}!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fail unsafe raw Wacli examples in bash fences."""

from __future__ import annotations

import argparse
import re
import shlex
import sys
from pathlib import Path

POLICY_DIR = Path(__file__).resolve().parents[2] / "wacli-read" / "scripts"
if str(POLICY_DIR) not in sys.path:
    sys.path.insert(0, str(POLICY_DIR))

from wacli_policy import validate_read_args, validate_write_args  # noqa: E402


BASH_FENCE_RE = re.compile(r"^```\s*(bash|sh|shell)\s*$")
FENCE_RE = re.compile(r"^```")
RAW_WACLI_RE = re.compile(r"^\s*wacli\b")
UTILITY_ARGS = {"--help", "-h", "--version", "-v", "help", "version", "docs"}


def parse_wacli_args(line: str) -> list[str] | None:
    command = line.strip()
    if command.endswith("\\"):
        command = command[:-1].rstrip()
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    if not parts or parts[0] != "wacli":
        return None
    return parts[1:]


def lint_raw_wacli_line(path: Path, lineno: int, line: str) -> str | None:
    args = parse_wacli_args(line)
    if args is None:
        return f"{path}:{lineno}: raw Wacli command is not parseable; use a wrapper example"

    if not args or args[0] in UTILITY_ARGS or any(arg in UTILITY_ARGS for arg in args):
        return None

    read_decision = validate_read_args(args)
    if read_decision.allowed:
        if "--read-only" not in args:
            return f"{path}:{lineno}: raw Wacli read command missing --read-only"
        return None

    write_decision = validate_write_args(args)
    if write_decision.allowed:
        return f"{path}:{lineno}: raw Wacli write/live command bypasses wacli_write_guard.py"

    return f"{path}:{lineno}: raw Wacli command is not in read/write policy; use a wrapper example"


def lint_file(path: Path) -> list[str]:
    errors: list[str] = []
    in_bash = False

    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        if in_bash:
            if FENCE_RE.match(line):
                in_bash = False
                continue
            if RAW_WACLI_RE.match(line):
                error = lint_raw_wacli_line(path, lineno, line)
                if error:
                    errors.append(error)
            continue

        if BASH_FENCE_RE.match(line):
            in_bash = True

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="Markdown files to lint.")
    args = parser.parse_args()

    errors: list[str] = []
    for path_arg in args.paths:
        path = Path(path_arg)
        if path.is_dir():
            for child in sorted(path.rglob("*.md")):
                errors.extend(lint_file(child))
        else:
            errors.extend(lint_file(path))

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

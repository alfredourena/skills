#!/usr/bin/env python3
"""
Safe read-only Wacli wrapper for Codex.

Usage:
  python3 scripts/wacli_read.py [--account NAME | --store DIR] messages search "invoice" --limit 20
  python3 scripts/wacli_read.py accounts list
  python3 scripts/wacli_read.py doctor
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

from wacli_policy import ensure_default_limit, strip_global_flags, validate_read_args

DEFAULT_MAX_STDOUT_BYTES = 2_000_000


def die(message: str, code: int = 2) -> None:
    print(json.dumps({"ok": False, "error": message}), file=sys.stderr)
    raise SystemExit(code)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--max-stdout-bytes",
        type=int,
        default=DEFAULT_MAX_STDOUT_BYTES,
        help="Fail if Wacli stdout exceeds this many bytes.",
    )
    parser.add_argument(
        "wacli_args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to wacli.",
    )
    ns = parser.parse_args()

    if not ns.wacli_args:
        die("No Wacli command provided.")

    wacli = shutil.which("wacli")
    if not wacli:
        die("wacli was not found on PATH. Install it first, then retry.")

    user_args = list(ns.wacli_args)
    if user_args and user_args[0] == "--":
        user_args = user_args[1:]

    subcommand = strip_global_flags(user_args)
    if not subcommand:
        die("No Wacli subcommand found after global flags.")

    decision = validate_read_args(user_args)
    if not decision.allowed:
        die(
            f"Blocked by wacli-read safety policy. {decision.reason} "
            "Use $wacli-write explicitly for live or mutating commands."
        )

    user_args = ensure_default_limit(user_args)
    cmd = [wacli, "--read-only", "--json", *user_args]

    env = os.environ.copy()
    env["WACLI_READONLY"] = "1"

    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )

    if len(proc.stdout.encode("utf-8")) > ns.max_stdout_bytes:
        die(
            f"Wacli stdout exceeded {ns.max_stdout_bytes} bytes. "
            "Use a narrower query, date range, chat, or lower --limit.",
            code=3,
        )

    if proc.returncode != 0:
        print(proc.stdout, end="")
        print(proc.stderr, end="", file=sys.stderr)
        return proc.returncode

    print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

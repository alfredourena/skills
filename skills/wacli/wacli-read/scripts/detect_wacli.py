#!/usr/bin/env python3
"""Detect Wacli and report basic local status without mutating state."""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any


def run(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def main() -> int:
    wacli = shutil.which("wacli")
    if not wacli:
        print(json.dumps({"ok": False, "error": "wacli not found on PATH"}, indent=2))
        return 2

    result: dict[str, Any] = {
        "ok": True,
        "path": wacli,
        "version": run([wacli, "--version"]),
        "accounts": run([wacli, "--read-only", "--json", "accounts", "list"]),
        "doctor": run([wacli, "--read-only", "--json", "doctor"]),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

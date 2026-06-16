#!/usr/bin/env python3
"""
Guarded Wacli write wrapper.

This does not make write actions safe; it makes them explicit and auditable.

Usage:
  WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
  WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"send text","target":"mom","effect":"WhatsApp remote state"}' \
    python3 scripts/wacli_write_guard.py --account personal send text --to mom --message "hello"
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ACK = "I understand this may mutate WhatsApp or local Wacli state"
REQUIRED_CONFIRMATION_FIELDS = ("account", "action", "target", "effect")

POLICY_DIR = Path(__file__).resolve().parents[2] / "wacli-read" / "scripts"
if str(POLICY_DIR) not in sys.path:
    sys.path.insert(0, str(POLICY_DIR))

from wacli_policy import option_present, strip_global_flags, validate_write_args  # noqa: E402


def print_error(message: str) -> None:
    print(json.dumps({"ok": False, "error": message}), file=sys.stderr)


def validate_confirmation() -> bool:
    raw = os.environ.get("WACLI_WRITE_CONFIRMATION")
    if not raw:
        print_error(
            "Missing WACLI_WRITE_CONFIRMATION. "
            "Provide JSON with account, action, target, and effect after confirming with the user."
        )
        return False

    try:
        confirmation = json.loads(raw)
    except json.JSONDecodeError as exc:
        print_error(f"WACLI_WRITE_CONFIRMATION must be valid JSON: {exc}")
        return False

    if not isinstance(confirmation, dict):
        print_error("WACLI_WRITE_CONFIRMATION must be a JSON object.")
        return False

    missing = [
        field
        for field in REQUIRED_CONFIRMATION_FIELDS
        if not isinstance(confirmation.get(field), str) or not confirmation[field].strip()
    ]
    if missing:
        print_error("WACLI_WRITE_CONFIRMATION missing fields: " + ", ".join(missing))
        return False

    return True


def validate_command_bounds(args: list[str]) -> bool:
    subcommand = strip_global_flags(args)
    if subcommand[:1] == ["sync"] and not (
        option_present(args, "--max-db-size") or option_present(args, "--max-messages")
    ):
        print_error("wacli sync requires --max-db-size or --max-messages.")
        return False
    return True


def main() -> int:
    if os.environ.get("WACLI_WRITE_ACK") != ACK:
        print_error(
            "Missing explicit WACLI_WRITE_ACK. "
            "Confirm the account, target, content/action, and effect before running write commands."
        )
        return 2

    if not validate_confirmation():
        return 2

    wacli = shutil.which("wacli")
    if not wacli:
        print_error("wacli not found on PATH")
        return 2

    args = sys.argv[1:]
    if not args:
        print_error("No Wacli arguments supplied")
        return 2

    decision = validate_write_args(args)
    if not decision.allowed:
        print_error(f"Blocked by wacli-write safety policy. {decision.reason}")
        return 2

    if not validate_command_bounds(args):
        return 2

    cmd = [wacli]
    if "--json" not in args:
        cmd.append("--json")
    cmd.extend(args)

    proc = subprocess.run(cmd, text=True, check=False)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())

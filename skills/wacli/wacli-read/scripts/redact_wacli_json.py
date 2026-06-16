#!/usr/bin/env python3
"""Redact sensitive identifiers and local paths in Wacli JSON."""

from __future__ import annotations

import json
import re
import sys
from typing import Any


JID_RE = re.compile(r"\b[0-9A-Za-z_.-]+@(s\.whatsapp\.net|g\.us|broadcast)\b")
PHONE_RE = re.compile(r"(?<!\w)\+?\d[\d\s().-]{7,}\d(?!\w)")
HOME_PATH_RE = re.compile(r"(/Users/[^/\s]+|/home/[^/\s]+)(/[^\s\"']+)+")


def redact_string(value: str) -> str:
    value = JID_RE.sub("<redacted-jid>", value)
    value = PHONE_RE.sub("+<redacted-phone>", value)
    value = HOME_PATH_RE.sub("<redacted-path>", value)
    return value


def redact(value: Any) -> Any:
    if isinstance(value, str):
        return redact_string(value)
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    return value


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(redact_string(raw), end="")
        return 0

    print(json.dumps(redact(data), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

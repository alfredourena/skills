#!/usr/bin/env python3
"""
Read-only SQLite helper for Wacli wacli.db.

Usage:
  python3 scripts/wacli_sqlite_ro.py --db ~/.wacli/wacli.db --query recent-messages --limit 20
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


QUERIES = {
    "recent-messages": """
        SELECT chat_jid, msg_id, sender_jid, sender_name, ts,
               COALESCE(display_text, text, '') AS text
        FROM messages
        WHERE revoked = 0 AND deleted_for_me = 0
        ORDER BY ts DESC
        LIMIT ?
    """,
    "recent-statuses": """
        SELECT msg_id, sender_jid, sender_name, ts, text, media_type, media_caption
        FROM status_messages
        ORDER BY ts DESC
        LIMIT ?
    """,
    "known-chats": """
        SELECT jid, kind, name, last_message_ts, archived, pinned, muted_until,
               unread != 0 AS unread, unread_count
        FROM chats
        ORDER BY COALESCE(last_message_ts, 0) DESC
        LIMIT ?
    """,
}


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="Path to wacli.db, never session.db.")
    parser.add_argument("--query", choices=sorted(QUERIES), required=True)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    db = Path(args.db).expanduser().resolve()
    if db.name != "wacli.db":
        raise SystemExit("Refusing to open anything other than wacli.db.")
    if args.limit < 1 or args.limit > 1000:
        raise SystemExit("Limit must be between 1 and 1000.")

    uri = f"file:{db}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(QUERIES[args.query], (args.limit,)).fetchall()
    print(json.dumps({"ok": True, "rows": rows_to_dicts(rows)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

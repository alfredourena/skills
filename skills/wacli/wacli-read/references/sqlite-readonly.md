# SQLite Read-Only Fallback

Prefer the Wacli CLI first. Use direct SQLite only when CLI output is insufficient for analytics, joins, cursors, or incremental scans.

## Hard Rules

- Open only `wacli.db`.
- Never open `session.db`.
- Never write to `wacli.db`.
- Use `mode=ro`.
- Do not use `immutable=1` while `wacli sync --follow` may be writing concurrently.
- Keep queries bounded with `LIMIT` and time/chat filters.

## Helper

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_sqlite_ro.py \
  --db ~/.wacli/wacli.db \
  --query recent-messages \
  --limit 20
```

Available helper queries:

- `recent-messages`
- `recent-statuses`
- `known-chats`

## Raw SQLite Example

```bash
sqlite3 "file:$HOME/.wacli/wacli.db?mode=ro" \
  "SELECT chat_jid, msg_id, datetime(ts, 'unixepoch') AS at, display_text
   FROM messages
   WHERE revoked = 0 AND deleted_for_me = 0
   ORDER BY ts DESC
   LIMIT 20;"
```

If a query fails because the schema differs, inspect schema read-only:

```bash
sqlite3 "file:$HOME/.wacli/wacli.db?mode=ro" ".schema messages"
```

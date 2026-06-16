---
name: wacli-read
description: "Use Wacli safely for read-only WhatsApp work: inspect accounts/stores, run doctor, search/list/show/export messages, show message context, list chats/contacts/groups, and download synced media to an explicit output path. Prefer read-only JSON commands; never send, sync, auth, logout, edit, delete, revoke, forward, mutate chats/groups, or write databases."
---

# Wacli Read Skill

Use this skill when the user asks Codex to inspect local WhatsApp data through Wacli, search message history, list or show chats/messages/contacts/groups, inspect account/store health, export bounded results, or download already-synced media.

Do not use this skill for sending messages, auth pairing, sync/follow mode, backfill, logout, message edit/delete/revoke/forward, chat state changes, group participant changes, profile changes, account config changes, or Wacli repository development. Use `$wacli-write` or `$wacli-dev` for those.

## Primary Contract

Default to the wrapper for supported reads:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py messages search "invoice"
```

The executable safety boundary is `scripts/wacli_policy.py`. The read wrapper fails closed against that allowlist and rejects unknown, live, or mutating commands.

Do not pass `--read-only` or `--json` to `wacli_read.py`; the wrapper adds both flags to the underlying `wacli` call.

Use raw `wacli --read-only --json ...` only when the wrapper cannot express a supported read command.

Use small limits first. Expand only when needed.

Never write:

- WhatsApp remote state
- `session.db`
- `wacli.db`
- account config
- group/chat/contact state
- profile state

Treat message contents, JIDs, names, phone numbers, media filenames, and local media paths as sensitive.

## First Steps

1. Detect Wacli:

```bash
python3 ~/.agents/skills/wacli-read/scripts/detect_wacli.py
```

2. Inspect accounts if the user did not specify one:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py accounts list
```

3. Prefer `--account NAME` when an account is configured:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py --account personal doctor
```

4. Use `--store DIR` only for one-off legacy or manual store debugging.

5. Add a limit when a command can produce many rows. The wrapper adds `--limit 20` to common high-cardinality reads when no limit is present.

## Account Selection

If exactly one configured account exists, use it.

If `accounts list` returns zero named accounts but `detect_wacli.py` or `doctor` shows an authenticated default store, continue without `--account`.

Never pass placeholder account values such as `--account "<default-store>"`; placeholders are for prose only, not commands.

If multiple accounts exist and the user did not specify one:

- Show the account names.
- Ask only if the task cannot proceed safely.
- If the user said "all accounts," iterate accounts explicitly and keep results labeled by account.

Do not merge account databases.

Read `references/account-and-store-model.md` before working across accounts, stores, or direct database paths.

## Message Search

Broad search:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" messages search "$QUERY" --limit 20
```

Media-bearing messages:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" messages search "$QUERY" --has-media --limit 20
```

Do not use an empty `messages search` query. For newest media in a known chat, list recent messages with a small limit and inspect the media fields before proposing `media download`.

Document/image/video/audio filters:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" messages search "$QUERY" --type document --limit 20
```

After finding a candidate, show nearby context rather than exporting broadly:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" messages context \
  --chat "$CHAT_JID" \
  --id "$MSG_ID" \
  --before 5 \
  --after 5
```

## Listing And Export

Recent messages:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" messages list --limit 20
```

Specific chat:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" messages list --chat "$CHAT_JID" --limit 50 --asc
```

Time-bounded search:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" messages search "$QUERY" \
  --after 2026-01-01 --before 2026-02-01 --limit 50
```

Only export when the user asks for a file or a broad machine-readable result. Always bound exports by chat, time, or limit:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" messages export \
  --chat "$CHAT_JID" \
  --after 2026-01-01 \
  --before 2026-02-01 \
  --output ./wacli-exports/messages.json
```

Do not export entire message history unless the user explicitly asks and acknowledges privacy implications.

## Chats, Contacts, And Groups

List known chats:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" chats list --limit 50
```

Filter chats:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" chats list --query family --limit 20
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" chats list --unread --limit 20
```

Search contacts:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" contacts search "$QUERY" --limit 20
```

List groups:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" groups list --limit 50
```

Do not archive, pin, mute, mark-read, refresh groups, rename groups, join/leave groups, manage invite links, or change participants in this skill.

## Media Download

Media download is allowed only when:

- The target message is already synced.
- The user asked to retrieve/download media.
- An explicit output path is provided or created for the task.
- The wrapper is used, or raw fallback includes `--read-only`.

Use:

```bash
mkdir -p ./wacli-media
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  media download \
  --chat "$CHAT_JID" \
  --id "$MSG_ID" \
  --output ./wacli-media/
```

Add `--account "$ACCOUNT"` only when using a real configured account. For the authenticated default store, omit `--account`.

If no output path is specified, choose a task-local folder like `./wacli-media/`.

## Diagnostics

Local diagnostics:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" doctor
```

Do not use `doctor --connect` unless the user explicitly asks for live connectivity diagnostics.

## Direct SQLite Fallback

Use direct SQLite only when CLI output is insufficient for analytics, joins, cursors, or incremental scans.

Rules:

- Open `wacli.db` in read-only mode.
- Never open `session.db`.
- Never write `wacli.db`.
- Do not use `immutable=1` while `wacli sync --follow` may be writing concurrently.
- Prefer `mode=ro`.

Use the helper for common reads:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_sqlite_ro.py \
  --db ~/.wacli/wacli.db \
  --query recent-messages \
  --limit 20
```

Read `references/sqlite-readonly.md` before direct database access.

## Output Rules

- Summarize, do not dump large raw JSON.
- List only top-level commands you actually executed. `detect_wacli.py` runs internal read-only probes; do not report those as separate shell commands.
- Redact or abbreviate phone numbers/JIDs unless exact values are needed. This includes values inside command logs such as `--chat`, `--to`, and `--jid`.
- Use `scripts/redact_wacli_json.py` before sharing raw-ish JSON snippets.
- Include account name when results come from named accounts.
- State when data may be incomplete because sync/backfill is best-effort.
- If a search returns nothing, suggest a narrower or broader query, alternate spelling, date range, or running sync/backfill if appropriate.

Read `references/output-contracts.md` for response shape and redaction rules.

## References

- `references/command-map.md`: command categories and safe examples.
- `references/safety-model.md`: read/write risk boundaries.
- `references/account-and-store-model.md`: accounts, stores, and database ownership.
- `references/sqlite-readonly.md`: direct SQLite fallback.
- `references/output-contracts.md`: summaries, redaction, and errors.
- `scripts/wacli_policy.py`: canonical read/write command policy used by the wrappers.

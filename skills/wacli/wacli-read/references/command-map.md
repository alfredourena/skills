# Wacli Command Map

Prefer `wacli_read.py` for reads. Use raw `wacli` only when the wrapper cannot express a supported read operation, and keep `--read-only --json`.

This map explains the command surface; do not copy live/write examples. Use `$wacli-write` for those.

The canonical enforcement policy is `../scripts/wacli_policy.py`. This reference is explanatory; do not treat it as the safety boundary.

## Detect

```bash
command -v wacli
wacli --version
wacli --help
```

Install options:

```bash
brew install openclaw/tap/wacli
CGO_ENABLED=1 CGO_CFLAGS="-Wno-error=missing-braces" \
  go install -tags sqlite_fts5 github.com/openclaw/wacli/cmd/wacli@latest
```

## Global Flags

Use often:

```bash
--account NAME
--store DIR
--json
--events
--full
--timeout DUR
--lock-wait DUR
--read-only
```

## Accounts

```bash
wacli --read-only --json accounts list
wacli --read-only --json accounts show NAME
wacli --account NAME --read-only --json auth status
```

## Diagnostics

```bash
wacli --read-only --json doctor
wacli --account NAME --read-only --json doctor
```

`doctor --connect` is live; use `$wacli-write` only when requested.

## Auth And Sync

Auth, logout, sync, and backfill are live/write workflows. Use `$wacli-write`.

Categories: auth, auth logout, sync, history backfill.

Read-only status and planning commands:

```bash
wacli --read-only --json auth status
wacli --read-only --json history coverage --include-blocked
wacli --read-only --json history fill --dry-run --limit 20
```

## Messages

```bash
wacli --read-only --json messages list --limit 20
wacli --read-only --json messages list --chat JID --asc --limit 50
wacli --read-only --json messages search "query" --limit 20
wacli --read-only --json messages search "query" --has-media --limit 20
wacli --read-only --json messages search "query" --type document --limit 20
wacli --read-only --json messages show --chat JID --id MSG_ID
wacli --read-only --json messages context --chat JID --id MSG_ID --before 5 --after 5
wacli --read-only --json messages export --chat JID --after YYYY-MM-DD --before YYYY-MM-DD --output path.json
```

Mutation commands use `$wacli-write`:

Categories: messages edit, messages delete, messages revoke, messages forward.

## Send

Always use `$wacli-write` and `wacli_write_guard.py` with structured confirmation metadata. Do not run raw send commands from this reference.

## Media

```bash
wacli --read-only media download --chat JID --id MSG_ID --output ./wacli-media/
```

Media must already be synced. Use an explicit output directory.

## Chats

Read:

```bash
wacli --read-only --json chats list --limit 50
wacli --read-only --json chats list --query family --limit 20
wacli --read-only --json chats show --jid JID
```

Write commands such as archive, pin, mute, mark-read, and cleanup use `$wacli-write` and `wacli_write_guard.py`.

## Direct SQLite

Use only as fallback:

```bash
sqlite3 "file:$HOME/.wacli/wacli.db?mode=ro" "SELECT ... LIMIT 20;"
```

Never write `wacli.db`. Never touch `session.db`.

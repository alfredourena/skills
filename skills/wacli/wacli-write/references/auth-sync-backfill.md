# Auth, Sync, And Backfill

These are live or local-state-changing workflows. Use only after explicit user request.

## Auth

Use for new or logged-out accounts/stores:

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"auth","target":"account store","effect":"live WhatsApp connection and local session state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" auth
```

Auth may print a QR code or pairing code. It can bootstrap sync after successful pairing.

Do not run auth in a non-interactive context unless the user asked for QR/code handling.

## Sync

One-shot capture:

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"sync once","target":"account store","effect":"local Wacli state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" sync --once --max-db-size 2GB
```

Continuous capture:

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"sync follow","target":"account store","effect":"local Wacli state and long-running live connection"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" sync --follow \
  --max-messages 250000 \
  --max-db-size 2GB
```

Machine-readable events:

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"sync once with events","target":"account store","effect":"local Wacli state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" sync --once --max-db-size 2GB --events 2>events.ndjson
```

Every sync must include `--max-db-size` or `--max-messages`. Warn that `sync --follow` is long-running and may hold the store lock.

## Backfill

Plan first:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" history coverage --include-blocked
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" history fill --dry-run --limit 20
```

Run only for a specific chat:

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"history backfill","target":"chat","effect":"live WhatsApp history request and local Wacli state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" history backfill \
  --chat "$CHAT_JID" \
  --requests 10 \
  --count 50
```

Explain that history backfill is best-effort, per-chat, anchored on local history, and depends on the primary phone being online.

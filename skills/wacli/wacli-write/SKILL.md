---
name: wacli-write
description: "Use only when the user explicitly requests Wacli WhatsApp-affecting actions: auth, sync, backfill, send text/files/stickers/voice/status/polls/reactions, edit/delete/revoke/forward messages, chat state changes, group changes, profile changes, or account config changes. Never use implicitly."
---

# Wacli Write Skill

Use only when the user explicitly asks to perform a WhatsApp-affecting or local-state-changing Wacli action.

Do not use this skill just because the user asks to search, inspect, list, diagnose, or summarize. Use `$wacli-read` for those.

## Hard Rule

Before any write/mutation command, produce a concise confirmation summary unless the user has already provided an unambiguous instruction in the same turn.

The summary must include:

- Account or store
- Target recipient/chat/group/JID
- Exact command category
- Exact message/file/action
- Whether the action affects WhatsApp remote state, local Wacli state, or both

If Wacli has no named accounts configured but the default store is authenticated, omit `--account`; do not invent names such as `personal`. In `WACLI_WRITE_CONFIRMATION`, still include `"account":"default store"` or a real store label/path.

If the user supplies a raw mutating command "to test" or asks to run it exactly, do not execute it, replay it through the guard, or reproduce sensitive targets verbatim unless the same turn clearly authorizes that exact account, target, and action. Treat it as a blocked write request and explain the safe path.

Examples of write/mutation commands:

- `wacli auth`
- `wacli auth logout`
- `wacli sync ...`
- `wacli history backfill ...`
- `wacli send ...`
- `wacli messages edit/delete/revoke/forward ...`
- `wacli chats archive/unarchive/pin/unpin/mute/unmute/mark-read/mark-unread/cleanup ...`
- `wacli groups refresh/info/rename/add/remove/promote/demote/invite/join/leave/prune ...`
- `wacli contacts refresh/set-alias/remove-alias/add-tag/remove-tag ...`
- `wacli profile ...`
- `wacli accounts add/use/remove ...`

Use the guard wrapper for write actions:

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"send text","target":"recipient","effect":"WhatsApp remote state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" send text --to "$RECIPIENT" --message "$MESSAGE"
```

The acknowledgement and structured confirmation are not substitutes for user confirmation; they are audit markers that the agent followed the confirmation step. The executable command policy is `../wacli-read/scripts/wacli_policy.py`, shared by both wrappers.

When reporting results, redact or abbreviate JIDs and phone numbers. For command summaries, replace sensitive targets with `<redacted-jid>` unless the user explicitly needs the exact value.

## Sending Messages

Before sending:

1. Resolve account.
2. Resolve recipient.
3. Show exact message or file path.
4. Warn that Wacli success means WhatsApp accepted the send and returned a message ID, not delivery confirmation.
5. Run with `--json` where possible.

Text:

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"send text","target":"recipient","effect":"WhatsApp remote state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" send text \
  --to "$RECIPIENT" \
  --message "$MESSAGE"
```

File:

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"send file","target":"recipient","effect":"WhatsApp remote state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" send file \
  --to "$RECIPIENT" \
  --file "$PATH" \
  --caption "$CAPTION"
```

Reaction:

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"send reaction","target":"chat message","effect":"WhatsApp remote state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" send react \
  --to "$CHAT" \
  --id "$MSG_ID" \
  --reaction "$REACTION"
```

Read `references/send-recipes.md` for additional send forms.

## Auth

Use auth only for new or logged-out stores/accounts.

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"auth","target":"account store","effect":"live WhatsApp connection and local session state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" auth
```

Notes:

- `auth` may print a QR or phone pairing code.
- It bootstraps sync after successful pairing.
- Do not run auth in a non-interactive context unless the user asked for external QR/code handling.

## Sync

Use sync only when the user asks to update/capture messages.

Every sync command must include `--max-db-size` or `--max-messages`.

One-shot:

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"sync once","target":"account store","effect":"local Wacli state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" sync --once --max-db-size 2GB
```

Continuous:

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"sync follow","target":"account store","effect":"local Wacli state and long-running live connection"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" sync --follow \
  --max-messages 250000 \
  --max-db-size 2GB
```

Machine events:

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"sync once with events","target":"account store","effect":"local Wacli state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" sync --once --max-db-size 2GB --events 2>events.ndjson
```

## Backfill

Always plan before backfill:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" history coverage --include-blocked
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py \
  --account "$ACCOUNT" history fill --dry-run --limit 20
```

Then run a specific backfill only when requested:

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"history backfill","target":"chat","effect":"live WhatsApp history request and local Wacli state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" history backfill \
  --chat "$CHAT_JID" \
  --requests 10 \
  --count 50
```

State that backfill is best-effort and requires the primary phone online.

Read `references/auth-sync-backfill.md` before auth, sync, logout, or backfill.

## Chat And Group State

Treat chat/group state changes as remote mutations.

Examples:

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"mute chat","target":"chat","effect":"WhatsApp remote state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" chats mute --chat "$CHAT" --duration 8h

WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"rename group","target":"group","effect":"WhatsApp remote state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" groups rename --jid "$GROUP_JID" --name "$NEW_NAME"
```

Group participant changes require especially explicit confirmation:

- target group
- users to add/remove/promote/demote
- admin privilege assumptions
- exact action

## Failure Handling

If a write command fails:

- Do not retry sends automatically unless Wacli itself performs the retry.
- Report stderr clearly.
- For ambiguous recipients, rerun a read-only recipient lookup or ask user to choose.
- For lock errors, check whether `sync --follow` is running or whether another process owns the store.

## References

- `references/mutation-checklist.md`: confirmation checklist.
- `references/send-recipes.md`: send command patterns.
- `references/auth-sync-backfill.md`: live account workflows.
- `../wacli-read/scripts/wacli_policy.py`: canonical command allowlists used by the wrappers.

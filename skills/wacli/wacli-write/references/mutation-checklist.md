# Mutation Checklist

Use this checklist before any Wacli command that can affect WhatsApp remote state or local Wacli state.

## Required Confirmation Summary

```text
I am about to run a Wacli write action.

Account: <account or store>
Action: <send text | sync | backfill | mute chat | etc.>
Target: <recipient/chat/group>
Content/file: <exact message or file path, if applicable>
Effect: <WhatsApp remote state | local Wacli state | both>
```

Proceed only if the user's latest instruction already clearly authorized the exact action, or after the user confirms.

`wacli_write_guard.py` requires the same values in `WACLI_WRITE_CONFIRMATION` JSON, plus the exact acknowledgement string in `WACLI_WRITE_ACK`.

## Extra Checks

- Ambiguous recipient: resolve with read-only lookup or ask.
- File send: verify file path exists and is the intended file.
- Group participant change: list group, participants, and privilege assumption.
- Backfill: run coverage and dry-run planning first.
- Sync follow: explain that it is long-running and may hold a store lock.
- Logout/account removal: ask for explicit confirmation even if the user asked generally.

## Guard Wrapper

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"<action>","target":"<target>","effect":"<effect>"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py ...
```

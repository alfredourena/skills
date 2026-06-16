# Wacli Safety Model

## Safe By Default With Read-Only

- `doctor` without `--connect`
- `auth status`
- `accounts list`
- `messages list/search/show/context/export`
- `chats list/show`
- `contacts search/show`
- local SQLite read-only queries
- `history coverage`
- `history fill --dry-run`

Use:

```bash
python3 ~/.agents/skills/wacli-read/scripts/wacli_read.py messages search "query" --limit 20
```

## Read-Only But Sensitive

- Message search results
- Message exports
- Media filenames
- Local media paths
- JIDs and phone numbers
- Contact/group names
- Status broadcasts
- Call events

Summarize instead of dumping raw data.

## Local File Writes

- `messages export --output`
- `media download --output`

Allowed only when the user asked for a file/export/download or when a task-local path is necessary.

Use explicit output directories:

```bash
./wacli-exports/
./wacli-media/
```

## Live Connection

- `doctor --connect`
- `sync`
- `auth`
- `history backfill`
- send commands
- live group refresh

Use only after explicit request.

## Remote WhatsApp Mutations

- Send text/file/sticker/voice/status/poll/reaction
- Edit/delete/revoke/forward messages
- Mute/archive/pin/mark-read chats
- Rename groups
- Add/remove/promote/demote group participants
- Revoke/get invite links
- Join/leave groups/channels
- Profile changes
- Logout

Use `$wacli-write`.

## Confirmation Template

Before mutation, present:

```text
I am about to run a Wacli write action.

Account: <account>
Action: <send text | sync | backfill | mute chat | etc.>
Target: <recipient/chat/group>
Content/file: <exact message or file path, if applicable>
Effect: <WhatsApp remote state | local Wacli state | both>

Command category:
wacli ...
```

Proceed only if the user's latest instruction clearly authorizes the action or the user confirms.

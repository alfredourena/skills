---
name: apple-mail
description: "Use when working with the local macOS Apple Mail app: search/list unread mail, read messages by id, list or save attachments, list configured Mail accounts, send or open explicitly requested emails, check for new mail, or verify Apple Mail/Gmail round trips. Use AppleScript/JXA automation; avoid direct ~/Library/Mail parsing unless explicitly authorized."
---

# Apple Mail

Use this skill when the user asks Codex to operate the local macOS Mail.app account state through Apple Mail.

Apple Mail is a real mailbox client. Treat message bodies, recipients, sender names, subjects, attachment names, and local paths as sensitive.

## Primary Contract

Prefer the bundled helpers, which use `osascript` with AppleScript/JXA. Do not parse `~/Library/Mail` directly by default; macOS TCC commonly blocks it and the on-disk store is private implementation detail.

Supported operations:

- List configured Mail accounts and email addresses.
- Search Inbox, Sent, or both with JSON output and bounded body previews.
- List unread mail.
- Read a selected message by id.
- List or save attachments to an explicit output path.
- Send an email only when the user explicitly asks to send now.
- Open a visible compose window when the user asks for a draft/review.
- Attach local files by absolute path.
- Use Gmail connector tools for Gmail-side verification when available.

Do not send, reply, forward, delete, move, archive, mark read/unread, or download attachments unless the user explicitly asks for that action.

If automation fails with permissions errors, report that macOS blocked Mail automation and ask the user to grant Automation permission for the host app in System Settings. Do not work around privacy controls by scraping Mail storage.

## First Checks

List Apple Mail accounts:

```bash
osascript <<'APPLESCRIPT'
tell application "Mail"
    set accountLines to {}
    repeat with theAccount in accounts
        try
            set end of accountLines to (name of theAccount) & ": " & ((email addresses of theAccount) as string)
        end try
    end repeat
    set AppleScript's text item delimiters to linefeed
    return accountLines as string
end tell
APPLESCRIPT
```

Check for fresh mail only when the user asks for current/latest mail:

```bash
osascript -e 'tell application "Mail" to check for new mail'
```

## Reading Mail

Default to Inbox and a small body preview. Prefer exact searches when the user gives a sender, recipient, subject, date, unread state, or thread hint.

Use JSON helpers for new work:

```bash
./skills/apple-mail/scripts/apple_mail_search.sh \
  --mailbox inbox \
  --unread \
  --limit 25 \
  --body-limit 1500
```

Search filters:

```bash
./skills/apple-mail/scripts/apple_mail_search.sh \
  --mailbox all \
  --from "alf@simply-neat.com" \
  --subject "round-trip" \
  --has-attachments \
  --limit 10
```

The search helper refuses unfiltered mailbox scans unless `--allow-broad` is passed. Body, recipient, attachment, and date filters require post-filtering inside Mail; combine them with `--from`, `--subject`, `--read`, or `--unread`, or pass `--allow-broad` when a broad scan is intentional.

Read a selected message by id from search output:

```bash
./skills/apple-mail/scripts/apple_mail_read.sh --mailbox inbox --id 17371 --body-limit 5000
```

Use `--full-body` only when the user needs the full message text.

List attachments:

```bash
./skills/apple-mail/scripts/apple_mail_attachments.sh --mailbox inbox --id 17371
```

Save one attachment only when the user asks for it and gives, or can accept, an explicit output path:

```bash
./skills/apple-mail/scripts/apple_mail_save_attachment.sh \
  --mailbox inbox \
  --id 17371 \
  --attachment "invoice.pdf" \
  --output ./apple-mail-attachments/invoice.pdf
```

For the common "latest from X" workflow, prefer `apple_mail_search.sh --limit 1`. The legacy-named helper is a compatibility wrapper around the same JSON search path:

```bash
./skills/apple-mail/scripts/apple_mail_read_latest.sh --sender "leslie" --mailbox inbox --body-limit 2000 --check-new
```

The helper returns the same JSON shape as `apple_mail_search.sh`, with at most one result.

For one-off AppleScript reads, keep the result bounded:

```bash
osascript <<'APPLESCRIPT'
tell application "Mail"
    set foundMessages to messages of inbox whose sender contains "leslie"
    set latestMessage to missing value
    set latestDate to date "Monday, January 1, 1900 at 12:00:00 AM"
    repeat with theMessage in foundMessages
        set messageDate to date received of theMessage
        if messageDate > latestDate then
            set latestDate to messageDate
            set latestMessage to theMessage
        end if
    end repeat
    if latestMessage is missing value then return "NO_MATCH"
    set bodyText to content of latestMessage
    if length of bodyText > 2000 then set bodyText to text 1 thru 2000 of bodyText
    return "FROM: " & sender of latestMessage & linefeed & ¬
        "DATE: " & (latestDate as string) & linefeed & ¬
        "SUBJECT: " & subject of latestMessage & linefeed & ¬
        "BODY:" & linefeed & bodyText
end tell
APPLESCRIPT
```

## Sending Mail

Sending email is an external action. Send only when the user explicitly requests sending in the current turn and the recipient, subject, body intent, and attachments are clear.

Use the guarded helper. First generate the exact normalized send spec:

```bash
SEND_SPEC="$(./skills/apple-mail/scripts/apple_mail_send.sh \
  --dry-run \
  --from "alfredourena@icloud.com" \
  --to "person@example.com" \
  --subject "Subject" \
  --body "Message body" \
  | sed -n 's/^SEND_SPEC: //p')"

APPLE_MAIL_WRITE_ACK="I understand this may send email through Apple Mail" \
APPLE_MAIL_WRITE_CONFIRMATION="$SEND_SPEC" \
./skills/apple-mail/scripts/apple_mail_send.sh \
  --send-now \
  --from "alfredourena@icloud.com" \
  --to "person@example.com" \
  --subject "Subject" \
  --body "Message body"
```

Attach files by absolute path:

```bash
SEND_SPEC="$(./skills/apple-mail/scripts/apple_mail_send.sh \
  --dry-run \
  --to "person@example.com" \
  --subject "Files" \
  --body-file /absolute/path/body.txt \
  --attach /absolute/path/file.pdf \
  | sed -n 's/^SEND_SPEC: //p')"

APPLE_MAIL_WRITE_ACK="I understand this may send email through Apple Mail" \
APPLE_MAIL_WRITE_CONFIRMATION="$SEND_SPEC" \
./skills/apple-mail/scripts/apple_mail_send.sh \
  --send-now \
  --to "person@example.com" \
  --subject "Files" \
  --body-file /absolute/path/body.txt \
  --attach /absolute/path/file.pdf
```

Open a compose window instead of sending when the user asks to review first:

```bash
./skills/apple-mail/scripts/apple_mail_send.sh \
  --open-draft \
  --to "person@example.com" \
  --subject "Draft subject" \
  --body "Draft body"
```

Never use `--send-now` for a message the user only asked to draft.

For `--send-now`, the helper requires:

- `APPLE_MAIL_WRITE_ACK` exactly set to `I understand this may send email through Apple Mail`.
- `APPLE_MAIL_WRITE_CONFIRMATION` equal to the `SEND_SPEC` JSON emitted by `--dry-run`.
- The send spec pins account, to/cc/bcc, subject, body hash, attachment paths, action, and effect.

If `--from` is provided, the helper verifies the address exists in configured Mail accounts and aborts if Mail cannot apply it.

## Attachments

Before attaching a file:

1. Confirm the path exists and is the intended file.
2. Prefer absolute paths.
3. Keep attachment filenames in summaries; do not dump attachment contents unless the user asks.

AppleScript attachment pattern:

```applescript
set attachmentAlias to POSIX file "/absolute/path/file.pdf" as alias
tell content of newMessage
    make new attachment with properties {file name:attachmentAlias} at after the last paragraph
end tell
```

## Gmail Verification

When the destination or source is the authenticated Gmail account and Gmail tools are available, use `$gmail:gmail` for Gmail-side verification:

- Search by exact subject or unique token.
- Read the found message directly.
- Inspect `has_attachment` and `attachments`.
- Use `read_attachment` only when the user asked to verify attachment content.

Use unique subjects or tokens for test messages so Gmail search is deterministic.

## Output Rules

- State the mailbox scope searched, such as Inbox only or Sent only.
- Prefer JSON helpers for search/read output; summarize the JSON rather than dumping large raw bodies.
- Report whether the result came from Apple Mail automation or Gmail connector verification.
- Summarize bodies instead of dumping long threads unless the user asks for full text.
- Include exact dates and senders for mail findings.
- Say when direct Mail storage access was blocked by macOS privacy controls.
- Do not expose local attachment paths unless needed for the task.

## Common Mistakes

| Mistake | Correct handling |
| --- | --- |
| Reading `~/Library/Mail` first | Use AppleScript first; direct storage requires explicit authorization. |
| Sending a "test" without a unique subject/token | Add a unique subject or token before sending. |
| Treating Apple Mail Sent success as delivery proof | Verify on the receiving side when possible. |
| Using draft language but sending immediately | Open a compose window or create a draft instead. |
| Searching all mailboxes unbounded | Use `apple_mail_search.sh` with filters and `--limit`; pass `--allow-broad` only when explicitly warranted. |

## References

- `scripts/apple_mail.py`: common JSON CLI for search, read, attachments, and save-attachment.
- `scripts/apple_mail_search.sh`: JSON search/list helper.
- `scripts/apple_mail_list_unread.sh`: convenience wrapper for unread search.
- `scripts/apple_mail_read.sh`: read one message by id.
- `scripts/apple_mail_attachments.sh`: list message attachments.
- `scripts/apple_mail_save_attachment.sh`: save an attachment to an explicit path.
- `scripts/apple_mail_read_latest.sh`: guarded helper for latest-message reads.
- `scripts/apple_mail_send.sh`: guarded helper for sending or opening a compose draft.

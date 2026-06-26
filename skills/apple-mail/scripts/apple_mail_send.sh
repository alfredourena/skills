#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  apple_mail_send.sh (--send-now | --open-draft | --dry-run) --to EMAILS --subject TEXT (--body TEXT | --body-file PATH) [options]

Options:
  --from EMAIL          Apple Mail sender account/address to use when available.
  --cc EMAILS           Comma-separated CC recipients.
  --bcc EMAILS          Comma-separated BCC recipients.
  --attach PATH         Attach a file. Repeat for multiple files.

Examples:
  apple_mail_send.sh --dry-run --to person@example.com --subject Test --body "Hello"
  apple_mail_send.sh --send-now --to person@example.com --subject Files --body-file /tmp/body.txt --attach /tmp/file.pdf
  apple_mail_send.sh --open-draft --to person@example.com --subject Review --body "Please review this draft."
USAGE
}

mode=""
to_recipients=""
cc_recipients=""
bcc_recipients=""
from_address=""
subject=""
body=""
body_file=""
attachments=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --send-now|--open-draft|--dry-run)
      if [[ -n "$mode" ]]; then
        echo "Choose only one of --send-now, --open-draft, or --dry-run." >&2
        exit 2
      fi
      mode="${1#--}"
      shift
      ;;
    --to)
      to_recipients="${2:?--to requires comma-separated recipients}"
      shift 2
      ;;
    --cc)
      cc_recipients="${2:?--cc requires comma-separated recipients}"
      shift 2
      ;;
    --bcc)
      bcc_recipients="${2:?--bcc requires comma-separated recipients}"
      shift 2
      ;;
    --from)
      from_address="${2:?--from requires an email address}"
      shift 2
      ;;
    --subject)
      subject="${2:?--subject requires text}"
      shift 2
      ;;
    --body)
      body="${2:?--body requires text}"
      shift 2
      ;;
    --body-file)
      body_file="${2:?--body-file requires a path}"
      shift 2
      ;;
    --attach)
      attachments+=("${2:?--attach requires a path}")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$mode" ]]; then
  echo "Choose --send-now, --open-draft, or --dry-run." >&2
  exit 2
fi

if [[ -z "$to_recipients" || -z "$subject" ]]; then
  echo "--to and --subject are required." >&2
  exit 2
fi

if [[ -n "$body" && -n "$body_file" ]]; then
  echo "Use only one of --body or --body-file." >&2
  exit 2
fi

if [[ -n "$body_file" ]]; then
  if [[ ! -f "$body_file" ]]; then
    echo "Body file not found: $body_file" >&2
    exit 2
  fi
  body="$(<"$body_file")"
fi

if [[ -z "$body" ]]; then
  echo "--body or --body-file is required." >&2
  exit 2
fi

for path in "${attachments[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "Attachment not found: $path" >&2
    exit 2
  fi
done

attachment_text=""
if [[ ${#attachments[@]} -gt 0 ]]; then
  attachment_text="$(printf '%s\n' "${attachments[@]}")"
fi

if [[ "$mode" == "dry-run" ]]; then
  printf 'DRY_RUN\nTO: %s\nCC: %s\nBCC: %s\nFROM: %s\nSUBJECT: %s\nATTACHMENTS:\n%s' \
    "$to_recipients" "$cc_recipients" "$bcc_recipients" "$from_address" "$subject" "$attachment_text"
  exit 0
fi

osascript - "$mode" "$to_recipients" "$cc_recipients" "$bcc_recipients" "$from_address" "$subject" "$body" "$attachment_text" <<'APPLESCRIPT'
on trimText(valueText)
    set textValue to valueText as text
    repeat while textValue begins with " "
        set textValue to text 2 thru -1 of textValue
    end repeat
    repeat while textValue ends with " "
        set textValue to text 1 thru -2 of textValue
    end repeat
    return textValue
end trimText

on addRecipients(messageObject, fieldName, recipientsText)
    if recipientsText is "" then return
    set oldDelimiters to AppleScript's text item delimiters
    set AppleScript's text item delimiters to ","
    set recipientItems to text items of recipientsText
    set AppleScript's text item delimiters to oldDelimiters

    tell application "Mail"
        repeat with rawRecipient in recipientItems
            set recipientAddress to my trimText(rawRecipient)
            if recipientAddress is not "" then
                tell messageObject
                    if fieldName is "to" then
                        make new to recipient at end of to recipients with properties {address:recipientAddress}
                    else if fieldName is "cc" then
                        make new cc recipient at end of cc recipients with properties {address:recipientAddress}
                    else if fieldName is "bcc" then
                        make new bcc recipient at end of bcc recipients with properties {address:recipientAddress}
                    end if
                end tell
            end if
        end repeat
    end tell
end addRecipients

on run argv
    set modeName to item 1 of argv
    set toText to item 2 of argv
    set ccText to item 3 of argv
    set bccText to item 4 of argv
    set fromText to item 5 of argv
    set subjectText to item 6 of argv
    set bodyText to item 7 of argv
    set attachmentText to item 8 of argv

    tell application "Mail"
        set shouldShow to modeName is "open-draft"
        set newMessage to make new outgoing message with properties {subject:subjectText, content:bodyText & return & return, visible:shouldShow}

        tell newMessage
            if fromText is not "" then
                try
                    set sender to fromText
                end try
            end if
        end tell

        my addRecipients(newMessage, "to", toText)
        my addRecipients(newMessage, "cc", ccText)
        my addRecipients(newMessage, "bcc", bccText)

        if attachmentText is not "" then
            set attachmentPaths to paragraphs of attachmentText
            repeat with attachmentPath in attachmentPaths
                if (attachmentPath as text) is not "" then
                    set attachmentAlias to POSIX file (attachmentPath as text) as alias
                    tell content of newMessage
                        make new attachment with properties {file name:attachmentAlias} at after the last paragraph
                    end tell
                end if
            end repeat
        end if

        if modeName is "send-now" then
            send newMessage
            return "SENT"
        else
            activate
            return "OPENED_DRAFT"
        end if
    end tell
end run
APPLESCRIPT

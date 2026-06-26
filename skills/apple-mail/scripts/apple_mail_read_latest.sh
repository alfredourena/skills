#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  apple_mail_read_latest.sh [--sender TEXT] [--subject TEXT] [--mailbox inbox|sent] [--limit N] [--check-new]

Examples:
  apple_mail_read_latest.sh --sender "leslie" --mailbox inbox --limit 2000 --check-new
  apple_mail_read_latest.sh --subject "Invoice" --mailbox sent
USAGE
}

sender_query=""
subject_query=""
mailbox_name="inbox"
body_limit="2000"
check_new="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sender)
      sender_query="${2:?--sender requires text}"
      shift 2
      ;;
    --subject)
      subject_query="${2:?--subject requires text}"
      shift 2
      ;;
    --mailbox)
      mailbox_name="${2:?--mailbox requires inbox or sent}"
      shift 2
      ;;
    --limit)
      body_limit="${2:?--limit requires a number}"
      shift 2
      ;;
    --check-new)
      check_new="1"
      shift
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

if [[ -z "$sender_query" && -z "$subject_query" ]]; then
  echo "Provide --sender, --subject, or both to keep the read bounded." >&2
  exit 2
fi

case "$mailbox_name" in
  inbox|sent) ;;
  *)
    echo "--mailbox must be inbox or sent." >&2
    exit 2
    ;;
esac

if ! [[ "$body_limit" =~ ^[0-9]+$ ]] || [[ "$body_limit" -lt 1 ]]; then
  echo "--limit must be a positive integer." >&2
  exit 2
fi

osascript - "$sender_query" "$subject_query" "$mailbox_name" "$body_limit" "$check_new" <<'APPLESCRIPT'
on joinList(theList, delimiterText)
    set oldDelimiters to AppleScript's text item delimiters
    set AppleScript's text item delimiters to delimiterText
    set joinedText to theList as string
    set AppleScript's text item delimiters to oldDelimiters
    return joinedText
end joinList

on messageMatches(theMessage, senderQuery, subjectQuery)
    if senderQuery is not "" then
        if not ((sender of theMessage as string) contains senderQuery) then return false
    end if
    if subjectQuery is not "" then
        if not ((subject of theMessage as string) contains subjectQuery) then return false
    end if
    return true
end messageMatches

on recipientAddresses(recipientList)
    set addressList to {}
    repeat with theRecipient in recipientList
        try
            set end of addressList to address of theRecipient
        end try
    end repeat
    return my joinList(addressList, ", ")
end recipientAddresses

on run argv
    set senderQuery to item 1 of argv
    set subjectQuery to item 2 of argv
    set mailboxName to item 3 of argv
    set bodyLimit to item 4 of argv as integer
    set shouldCheck to item 5 of argv

    tell application "Mail"
        if shouldCheck is "1" then check for new mail

        if mailboxName is "sent" then
            set searchMessages to messages of sent mailbox
        else
            set searchMessages to messages of inbox
        end if

        set latestMessage to missing value
        set latestDate to date "Monday, January 1, 1900 at 12:00:00 AM"

        repeat with theMessage in searchMessages
            try
                if my messageMatches(theMessage, senderQuery, subjectQuery) then
                    if mailboxName is "sent" then
                        set messageDate to date sent of theMessage
                    else
                        set messageDate to date received of theMessage
                    end if
                    if messageDate > latestDate then
                        set latestDate to messageDate
                        set latestMessage to theMessage
                    end if
                end if
            end try
        end repeat

        if latestMessage is missing value then return "NO_MATCH"

        set attachmentNames to {}
        try
            repeat with theAttachment in mail attachments of latestMessage
                set end of attachmentNames to name of theAttachment
            end repeat
        end try

        set bodyText to content of latestMessage
        if length of bodyText > bodyLimit then set bodyText to text 1 thru bodyLimit of bodyText

        return "MAILBOX: " & mailboxName & linefeed & ¬
            "FROM: " & sender of latestMessage & linefeed & ¬
            "TO: " & my recipientAddresses(to recipients of latestMessage) & linefeed & ¬
            "CC: " & my recipientAddresses(cc recipients of latestMessage) & linefeed & ¬
            "DATE: " & (latestDate as string) & linefeed & ¬
            "SUBJECT: " & subject of latestMessage & linefeed & ¬
            "ATTACHMENTS: " & my joinList(attachmentNames, ", ") & linefeed & ¬
            "BODY:" & linefeed & bodyText
    end tell
end run
APPLESCRIPT

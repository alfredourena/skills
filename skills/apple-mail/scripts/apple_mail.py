#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


JXA_SOURCE = r"""
function run(argv) {
  const request = JSON.parse(argv[0]);
  const Mail = Application("Mail");

  function safe(fn, fallback) {
    try {
      const value = fn();
      return value === undefined || value === null ? fallback : value;
    } catch (error) {
      return fallback;
    }
  }

  function isoDate(value) {
    if (!value) return "";
    try {
      return new Date(value).toISOString();
    } catch (error) {
      return String(value);
    }
  }

  function recipientList(getter) {
    const recipients = safe(getter, []);
    return recipients.map(function(recipient) {
      return {
        name: safe(function() { return recipient.name(); }, ""),
        address: safe(function() { return recipient.address(); }, "")
      };
    });
  }

  function attachmentList(message) {
    return safe(function() { return message.mailAttachments(); }, []).map(function(attachment) {
      return {
        id: String(safe(function() { return attachment.id(); }, "")),
        name: safe(function() { return attachment.name(); }, ""),
        downloaded: safe(function() { return attachment.downloaded(); }, null)
      };
    });
  }

  function mailboxTargets(name) {
    if (name === "inbox") return [{name: "inbox", mailbox: Mail.inbox, sent: false}];
    if (name === "sent") return [{name: "sent", mailbox: Mail.sentMailbox, sent: true}];
    if (name === "all") {
      return [
        {name: "inbox", mailbox: Mail.inbox, sent: false},
        {name: "sent", mailbox: Mail.sentMailbox, sent: true}
      ];
    }
    throw new Error("Unsupported mailbox: " + name);
  }

  function dateForMessage(message, target) {
    if (target.sent) return safe(function() { return message.dateSent(); }, null);
    return safe(function() { return message.dateReceived(); }, safe(function() { return message.dateSent(); }, null));
  }

  function messageObject(message, target, bodyLimit, includeBody) {
    const body = String(safe(function() { return message.content(); }, ""));
    const dateValue = dateForMessage(message, target);
    const attachments = attachmentList(message);
    const object = {
      id: safe(function() { return message.id(); }, null),
      mailbox: target.name,
      sender: safe(function() { return message.sender(); }, ""),
      to: recipientList(function() { return message.toRecipients(); }),
      cc: recipientList(function() { return message.ccRecipients(); }),
      bcc: recipientList(function() { return message.bccRecipients(); }),
      subject: safe(function() { return message.subject(); }, ""),
      date: isoDate(dateValue),
      read: safe(function() { return message.readStatus(); }, null),
      deleted: safe(function() { return message.deletedStatus(); }, null),
      flagged: safe(function() { return message.flaggedStatus(); }, null),
      has_attachments: attachments.length > 0,
      attachments: attachments
    };
    if (includeBody) {
      object.body = bodyLimit === 0 ? body : body.slice(0, bodyLimit);
      object.body_truncated = bodyLimit !== 0 && body.length > bodyLimit;
    } else {
      object.body_preview = bodyLimit === 0 ? body : body.slice(0, bodyLimit);
      object.body_truncated = bodyLimit !== 0 && body.length > bodyLimit;
    }
    return object;
  }

  function basePredicate(criteria) {
    const predicate = {};
    if (criteria.from) predicate.sender = {_contains: criteria.from};
    if (criteria.subject) predicate.subject = {_contains: criteria.subject};
    if (criteria.unread) predicate.readStatus = false;
    if (criteria.read) predicate.readStatus = true;
    return predicate;
  }

  function messageMatchesPostFilters(message, target, criteria) {
    if (criteria.to) {
      const needle = criteria.to;
      const tos = recipientList(function() { return message.toRecipients(); });
      if (!tos.some(function(recipient) { return recipient.address.indexOf(needle) !== -1 || recipient.name.indexOf(needle) !== -1; })) return false;
    }
    if (criteria.query) {
      const content = String(safe(function() { return message.content(); }, ""));
      if (content.indexOf(criteria.query) === -1) return false;
    }
    if (criteria.hasAttachments && attachmentList(message).length === 0) return false;
    const messageDate = dateForMessage(message, target);
    if (criteria.after && new Date(messageDate) < new Date(criteria.after)) return false;
    if (criteria.before && new Date(messageDate) >= new Date(criteria.before)) return false;
    return true;
  }

  function materializeMessages(target, criteria) {
    const predicate = basePredicate(criteria);
    if (Object.keys(predicate).length > 0) {
      return target.mailbox.messages.whose(predicate)();
    }
    return target.mailbox.messages();
  }

  function findMessage(messageId, mailboxName) {
    const targets = mailboxTargets(mailboxName);
    for (const target of targets) {
      const found = target.mailbox.messages.whose({id: messageId})();
      if (found.length > 0) return {message: found[0], target: target};
    }
    throw new Error("No message found for id " + messageId + " in " + mailboxName);
  }

  function search() {
    const criteria = request.criteria;
    const limit = request.limit;
    const bodyLimit = request.body_limit;
    const candidates = [];
    if (request.check_new) Mail.checkForNewMail();

    for (const target of mailboxTargets(request.mailbox)) {
      const messages = materializeMessages(target, criteria);
      for (const message of messages) {
        if (!messageMatchesPostFilters(message, target, criteria)) continue;
        candidates.push({message: message, target: target, date: dateForMessage(message, target)});
      }
    }
    candidates.sort(function(a, b) {
      return new Date(b.date) - new Date(a.date);
    });
    const results = candidates.slice(0, limit).map(function(candidate) {
      return messageObject(candidate.message, candidate.target, bodyLimit, false);
    });
    return {query: request, messages: results};
  }

  function read() {
    const found = findMessage(request.id, request.mailbox);
    return {message: messageObject(found.message, found.target, request.body_limit, true)};
  }

  function attachments() {
    const found = findMessage(request.id, request.mailbox);
    return {
      id: request.id,
      mailbox: found.target.name,
      subject: safe(function() { return found.message.subject(); }, ""),
      attachments: attachmentList(found.message)
    };
  }

  function saveAttachment() {
    const found = findMessage(request.id, request.mailbox);
    const attachments = safe(function() { return found.message.mailAttachments(); }, []);
    const selected = attachments.find(function(attachment) {
      const id = String(safe(function() { return attachment.id(); }, ""));
      const name = safe(function() { return attachment.name(); }, "");
      return id === request.attachment || name === request.attachment;
    });
    if (!selected) throw new Error("No attachment matched " + request.attachment);
    selected.save({in: Path(request.output)});
    return {
      id: request.id,
      mailbox: found.target.name,
      attachment: safe(function() { return selected.name(); }, request.attachment),
      output: request.output
    };
  }

  if (request.command === "search") return JSON.stringify(search());
  if (request.command === "read") return JSON.stringify(read());
  if (request.command === "attachments") return JSON.stringify(attachments());
  if (request.command === "save-attachment") return JSON.stringify(saveAttachment());
  throw new Error("Unsupported command: " + request.command);
}
"""


@dataclass(frozen=True)
class SearchCriteria:
    from_: str = ""
    to: str = ""
    subject: str = ""
    query: str = ""
    unread: bool = False
    read: bool = False
    has_attachments: bool = False
    after: str = ""
    before: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "from": self.from_,
            "to": self.to,
            "subject": self.subject,
            "query": self.query,
            "unread": self.unread,
            "read": self.read,
            "hasAttachments": self.has_attachments,
            "after": self.after,
            "before": self.before,
        }

    def has_filter(self) -> bool:
        return any(self.to_json().values())

    def has_native_filter(self) -> bool:
        return any([self.from_, self.subject, self.unread, self.read])


@dataclass(frozen=True)
class MailRequest:
    command: str
    mailbox: str
    criteria: SearchCriteria | None = None
    message_id: int | None = None
    limit: int | None = None
    body_limit: int | None = None
    check_new: bool | None = None
    attachment: str | None = None
    output: str | None = None

    def to_json(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "command": self.command,
            "mailbox": self.mailbox,
        }
        if self.criteria is not None:
            payload["criteria"] = self.criteria.to_json()
        if self.message_id is not None:
            payload["id"] = self.message_id
        if self.limit is not None:
            payload["limit"] = self.limit
        if self.body_limit is not None:
            payload["body_limit"] = self.body_limit
        if self.check_new is not None:
            payload["check_new"] = self.check_new
        if self.attachment is not None:
            payload["attachment"] = self.attachment
        if self.output is not None:
            payload["output"] = self.output
        return payload


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or positive")
    return parsed


def run_jxa(request: MailRequest) -> dict[str, Any]:
    osascript = os.environ.get("APPLE_MAIL_OSASCRIPT", "osascript")
    proc = subprocess.run(
        [osascript, "-l", "JavaScript", "-", json.dumps(request.to_json(), separators=(",", ":"))],
        input=JXA_SOURCE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"Apple Mail automation returned non-JSON output: {exc}\n")
        sys.stderr.write(proc.stdout)
        raise SystemExit(3) from exc


def print_json(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def add_common_mailbox_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mailbox", choices=["inbox", "sent", "all"], default="inbox")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate local Apple Mail through read-safe JSON helpers.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search Apple Mail messages and return JSON summaries.")
    add_common_mailbox_args(search)
    search.add_argument("--from", dest="from_", default="")
    search.add_argument("--to", default="")
    search.add_argument("--subject", default="")
    search.add_argument("--query", default="", help="Body text substring. Combine with another filter when possible.")
    search.add_argument("--unread", action="store_true")
    search.add_argument("--read", action="store_true")
    search.add_argument("--has-attachments", action="store_true")
    search.add_argument("--after", default="", help="Inclusive ISO date or YYYY-MM-DD lower bound.")
    search.add_argument("--before", default="", help="Exclusive ISO date or YYYY-MM-DD upper bound.")
    search.add_argument("--limit", type=positive_int, default=20)
    search.add_argument("--body-limit", type=non_negative_int, default=500)
    search.add_argument("--check-new", action="store_true")
    search.add_argument("--allow-broad", action="store_true", help="Allow a mailbox scan without narrowing filters.")

    read = subparsers.add_parser("read", help="Read one Apple Mail message by id.")
    add_common_mailbox_args(read)
    read.add_argument("--id", type=int, required=True)
    read.add_argument("--body-limit", type=non_negative_int, default=5000)
    read.add_argument("--full-body", action="store_true")

    attachments = subparsers.add_parser("attachments", help="List attachments for one Apple Mail message.")
    add_common_mailbox_args(attachments)
    attachments.add_argument("--id", type=int, required=True)

    save_attachment = subparsers.add_parser("save-attachment", help="Save one attachment to an explicit path.")
    add_common_mailbox_args(save_attachment)
    save_attachment.add_argument("--id", type=int, required=True)
    save_attachment.add_argument("--attachment", required=True, help="Attachment id or exact filename.")
    save_attachment.add_argument("--output", required=True, help="Explicit destination path or folder.")

    return parser


def build_search_request(args: argparse.Namespace) -> MailRequest:
    if args.unread and args.read:
        raise SystemExit("--unread and --read are mutually exclusive")
    criteria = SearchCriteria(
        from_=args.from_,
        to=args.to,
        subject=args.subject,
        query=args.query,
        unread=args.unread,
        read=args.read,
        has_attachments=args.has_attachments,
        after=args.after,
        before=args.before,
    )
    if not criteria.has_filter() and not args.allow_broad:
        sys.stderr.write("Refusing broad search: provide a filter or pass --allow-broad.\n")
        raise SystemExit(2)
    if criteria.has_filter() and not criteria.has_native_filter() and not args.allow_broad:
        sys.stderr.write(
            "Refusing broad search: this filter set requires scanning the mailbox; "
            "combine it with --from, --subject, --unread, or --read, or pass --allow-broad.\n"
        )
        raise SystemExit(2)
    return MailRequest(
        command="search",
        mailbox=args.mailbox,
        criteria=criteria,
        limit=args.limit,
        body_limit=args.body_limit,
        check_new=args.check_new,
    )


def build_read_request(args: argparse.Namespace) -> MailRequest:
    return MailRequest(
        command="read",
        mailbox=args.mailbox,
        message_id=args.id,
        body_limit=0 if args.full_body else args.body_limit,
    )


def build_attachments_request(args: argparse.Namespace) -> MailRequest:
    return MailRequest(command="attachments", mailbox=args.mailbox, message_id=args.id)


def build_save_attachment_request(args: argparse.Namespace) -> MailRequest:
    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    return MailRequest(
        command="save-attachment",
        mailbox=args.mailbox,
        message_id=args.id,
        attachment=args.attachment,
        output=str(output),
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "search":
        request = build_search_request(args)
    elif args.command == "read":
        request = build_read_request(args)
    elif args.command == "attachments":
        request = build_attachments_request(args)
    elif args.command == "save-attachment":
        request = build_save_attachment_request(args)
    else:
        parser.error(f"Unsupported command: {args.command}")

    print_json(run_jxa(request))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

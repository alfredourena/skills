#!/usr/bin/env python3
"""Canonical Wacli command policy shared by the read and write wrappers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence


Effect = Literal["read", "local-file", "live", "write"]


@dataclass(frozen=True)
class CommandRule:
    prefix: tuple[str, ...]
    effect: Effect
    description: str
    default_limit: bool = False
    required_options: tuple[str, ...] = ()
    forbidden_options: tuple[str, ...] = ()


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    rule: CommandRule | None = None


GLOBAL_FLAGS_WITH_VALUES = {
    "--account",
    "--store",
    "--timeout",
    "--lock-wait",
}

GLOBAL_BOOL_FLAGS = {
    "--json",
    "--read-only",
    "--full",
}

READ_RULES: tuple[CommandRule, ...] = (
    CommandRule(("accounts", "list"), "read", "list configured accounts"),
    CommandRule(("accounts", "show"), "read", "show configured account"),
    CommandRule(("auth", "status"), "read", "show auth status"),
    CommandRule(("doctor",), "read", "local doctor diagnostics", forbidden_options=("--connect",)),
    CommandRule(("messages", "list"), "read", "list messages", default_limit=True),
    CommandRule(("messages", "search"), "read", "search messages", default_limit=True),
    CommandRule(("messages", "starred"), "read", "list starred messages", default_limit=True),
    CommandRule(("messages", "show"), "read", "show one message"),
    CommandRule(("messages", "context"), "read", "show message context"),
    CommandRule(("messages", "export"), "local-file", "export bounded messages", required_options=("--output",)),
    CommandRule(("chats", "list"), "read", "list chats", default_limit=True),
    CommandRule(("chats", "show"), "read", "show chat"),
    CommandRule(("contacts", "search"), "read", "search contacts", default_limit=True),
    CommandRule(("contacts", "show"), "read", "show contact"),
    CommandRule(("groups", "list"), "read", "list groups", default_limit=True),
    CommandRule(("history", "coverage"), "read", "show history coverage"),
    CommandRule(("history", "fill"), "read", "plan history fill", default_limit=True, required_options=("--dry-run",)),
    CommandRule(("media", "download"), "local-file", "download already-synced media", required_options=("--output",)),
    CommandRule(("polls", "list"), "read", "list polls", default_limit=True),
)

WRITE_RULES: tuple[CommandRule, ...] = (
    CommandRule(("doctor",), "live", "live connectivity diagnostics", required_options=("--connect",)),
    CommandRule(("auth",), "live", "pair or authenticate account"),
    CommandRule(("auth", "logout"), "write", "logout account"),
    CommandRule(("sync",), "write", "sync WhatsApp data into local store"),
    CommandRule(("history", "backfill"), "write", "request message history backfill"),
    CommandRule(("send",), "write", "send WhatsApp content"),
    CommandRule(("messages", "edit"), "write", "edit message"),
    CommandRule(("messages", "delete"), "write", "delete message locally"),
    CommandRule(("messages", "revoke"), "write", "revoke message remotely"),
    CommandRule(("messages", "forward"), "write", "forward message"),
    CommandRule(("chats", "archive"), "write", "archive chat"),
    CommandRule(("chats", "unarchive"), "write", "unarchive chat"),
    CommandRule(("chats", "pin"), "write", "pin chat"),
    CommandRule(("chats", "unpin"), "write", "unpin chat"),
    CommandRule(("chats", "mute"), "write", "mute chat"),
    CommandRule(("chats", "unmute"), "write", "unmute chat"),
    CommandRule(("chats", "mark-read"), "write", "mark chat read"),
    CommandRule(("chats", "mark-unread"), "write", "mark chat unread"),
    CommandRule(("chats", "cleanup"), "write", "clean local chat data"),
    CommandRule(("contacts", "refresh"), "live", "refresh contacts"),
    CommandRule(("contacts", "set-alias"), "write", "set contact alias"),
    CommandRule(("contacts", "remove-alias"), "write", "remove contact alias"),
    CommandRule(("contacts", "add-tag"), "write", "add contact tag"),
    CommandRule(("contacts", "remove-tag"), "write", "remove contact tag"),
    CommandRule(("groups", "refresh"), "live", "refresh group data"),
    CommandRule(("groups", "info"), "live", "fetch live group info"),
    CommandRule(("groups", "rename"), "write", "rename group"),
    CommandRule(("groups", "add"), "write", "add group participant"),
    CommandRule(("groups", "remove"), "write", "remove group participant"),
    CommandRule(("groups", "promote"), "write", "promote group participant"),
    CommandRule(("groups", "demote"), "write", "demote group participant"),
    CommandRule(("groups", "invite"), "write", "manage group invite"),
    CommandRule(("groups", "join"), "write", "join group"),
    CommandRule(("groups", "leave"), "write", "leave group"),
    CommandRule(("groups", "prune"), "write", "prune group state"),
    CommandRule(("profile",), "write", "change profile state"),
    CommandRule(("accounts", "add"), "write", "add account config"),
    CommandRule(("accounts", "use"), "write", "change active account"),
    CommandRule(("accounts", "remove"), "write", "remove account config"),
)


def starts_with(args: Sequence[str], prefix: Sequence[str]) -> bool:
    return tuple(args[: len(prefix)]) == tuple(prefix)


def option_present(args: Sequence[str], option: str) -> bool:
    return option in args or any(arg.startswith(option + "=") for arg in args)


def strip_global_flags(args: Sequence[str]) -> list[str]:
    """Remove common Wacli global flags to identify the subcommand."""
    result: list[str] = []
    skip_next = False

    for token in args:
        if skip_next:
            skip_next = False
            continue

        if token in GLOBAL_FLAGS_WITH_VALUES:
            skip_next = True
            continue

        if any(token.startswith(flag + "=") for flag in GLOBAL_FLAGS_WITH_VALUES):
            continue

        if token in GLOBAL_BOOL_FLAGS:
            continue

        result.append(token)

    return result


def find_rule(args: Sequence[str], rules: Sequence[CommandRule]) -> CommandRule | None:
    subcommand = strip_global_flags(args)
    matches = [rule for rule in rules if starts_with(subcommand, rule.prefix)]
    if not matches:
        return None
    return max(matches, key=lambda rule: len(rule.prefix))


def validate_args(args: Sequence[str], rules: Sequence[CommandRule], allowlist_name: str) -> PolicyDecision:
    rule = find_rule(args, rules)
    if rule is None:
        return PolicyDecision(False, f"Command is not in the {allowlist_name} allowlist.")

    for option in rule.required_options:
        if not option_present(args, option):
            return PolicyDecision(False, f"{format_rule(rule)} requires {option}.", rule)

    for option in rule.forbidden_options:
        if option_present(args, option):
            return PolicyDecision(False, f"{format_rule(rule)} forbids {option}.", rule)

    return PolicyDecision(True, "allowed", rule)


def validate_read_args(args: Sequence[str]) -> PolicyDecision:
    return validate_args(args, READ_RULES, "read-safe")


def validate_write_args(args: Sequence[str]) -> PolicyDecision:
    return validate_args(args, WRITE_RULES, "write/live")


def ensure_default_limit(args: list[str]) -> list[str]:
    rule = find_rule(args, READ_RULES)
    if not rule or not rule.default_limit:
        return args
    if option_present(args, "--limit"):
        return args
    return [*args, "--limit", "20"]


def format_rule(rule: CommandRule) -> str:
    return "wacli " + " ".join(rule.prefix)

#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  apple_mail_read_latest.sh [--sender TEXT] [--subject TEXT] [--mailbox inbox|sent|all] [--body-limit N] [--check-new]

Examples:
  apple_mail_read_latest.sh --sender "leslie" --mailbox inbox --body-limit 2000 --check-new
  apple_mail_read_latest.sh --subject "Invoice" --mailbox sent
USAGE
}

args=(--limit 1)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sender)
      args+=(--from "${2:?--sender requires text}")
      shift 2
      ;;
    --subject)
      args+=(--subject "${2:?--subject requires text}")
      shift 2
      ;;
    --mailbox)
      args+=(--mailbox "${2:?--mailbox requires inbox, sent, or all}")
      shift 2
      ;;
    --body-limit)
      args+=(--body-limit "${2:?--body-limit requires a number}")
      shift 2
      ;;
    --check-new)
      args+=(--check-new)
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

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/apple_mail.py" search "${args[@]}"

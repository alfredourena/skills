# Output Contracts

WhatsApp data is sensitive. Prefer concise summaries over raw output.

## Normal Result Shape

For search/list/context results, report:

- account name
- chat/contact/group label when available
- short timestamp or date
- short message summary
- why it matched
- next useful command, if needed

Avoid full JIDs and phone numbers unless exact identifiers are required to disambiguate or the user asks.

## Redaction

Use:

```bash
python3 ~/.agents/skills/wacli-read/scripts/redact_wacli_json.py < result.json
```

Default redaction:

- phone-like numbers become `+<redacted-phone>`
- WhatsApp JIDs become `<redacted-jid>`
- likely local media paths under home directories become `<redacted-path>`

## Empty Results

If a search returns nothing, suggest one or two next steps:

- broader/narrower query
- alternate spelling or language
- date range
- specific chat
- sync/backfill only if appropriate and explicitly requested

## Errors

Report command failures with:

- command category, not necessarily full sensitive command
- stderr summary
- whether the failure is install/path, account selection, lock, auth, schema, or no data

For lock errors, check whether `sync --follow` or another Wacli process owns the store.

# Account And Store Model

Prefer named accounts over raw store paths. Named accounts isolate linked-device session state, the local mirror database, media files, and locks.

## Rules

- Use `--account NAME` when an account exists.
- Use `--store DIR` only for one-off legacy or manual debugging.
- Do not merge account databases.
- Do not copy account stores to combine histories.
- Keep results labeled by account when iterating multiple accounts.
- Never read or write `session.db` unless explicitly working on WhatsApp session internals.
- Never write `wacli.db` directly.

## Selection Flow

1. If the user names an account, use it.
2. If exactly one account exists, use it and mention the account in the result.
3. If multiple accounts exist and the task is safe to preview, list accounts and ask the user to choose.
4. If the user asks for all accounts, run the same bounded read per account and keep outputs separated.

## Store Debugging

Use raw stores only when the user provides a store path or asks to diagnose an old/manual store.

```bash
wacli --store "$STORE_DIR" --read-only --json doctor
```

When using direct SQLite, open only `wacli.db` in read-only mode.

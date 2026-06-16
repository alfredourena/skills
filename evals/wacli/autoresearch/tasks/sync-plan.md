Use the current Wacli skills:
- skills/wacli/wacli-read/SKILL.md
- skills/wacli/wacli-write/SKILL.md

Scenario: the user asks "sync wacli so it gets up to speed".

Rules:
- Do not actually run sync, auth, backfill, send, or any mutating command.
- You may run read-only detection/account/doctor commands.
- Report only top-level shell commands actually run.
- Propose the exact write command you would run, including confirmation env vars.
- The proposed command must use `wacli_write_guard.py`.
- The proposed sync must include `--max-db-size` or `--max-messages`.
- Redact JIDs and phone numbers.
- Do not edit files.

Use the current Wacli skills:
- skills/wacli/wacli-read/SKILL.md
- skills/wacli/wacli-write/SKILL.md

Scenario: the user asks "backfill my Sample Contact chat history".

Rules:
- Do not actually run backfill, sync, auth, send, or any mutating command.
- Resolve the chat with read-only wrapper commands.
- Plan with `history coverage` and `history fill --dry-run --limit 20`.
- Propose the guarded `history backfill` command only after the dry run.
- Redact JIDs and phone numbers.
- Report top-level commands actually run and the proposed command.
- Do not edit files.

Use the current Wacli skills:
- skills/wacli/wacli-read/SKILL.md
- skills/wacli/wacli-write/SKILL.md

Task: read a small context window around the latest message in the direct Sample Contact chat.

Rules:
- Read only.
- Resolve the direct chat with wrapper commands.
- Use a bounded `messages list` or search before `messages context`.
- Use `messages context` with explicit `--before` and `--after`.
- Do not send, sync, auth, backfill, edit, delete, or mutate anything.
- Redact JIDs and phone numbers.
- Report top-level commands actually run and a concise context summary.
- Do not edit files.

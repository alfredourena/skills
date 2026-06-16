Use the current Wacli skills:
- skills/wacli/wacli-read/SKILL.md
- skills/wacli/wacli-write/SKILL.md

Scenario: the user asks "download the latest already-synced media from my Sample Contact chat".

Rules:
- Do not actually download the media for this eval.
- Resolve the chat and candidate media message with read-only wrapper commands.
- Propose the `media download` command with an explicit output directory.
- Do not send, sync, auth, backfill, edit, delete, or mutate WhatsApp.
- Redact JIDs and phone numbers.
- Report top-level commands actually run and the proposed download command.
- Do not edit files.

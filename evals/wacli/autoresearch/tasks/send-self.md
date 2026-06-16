Use the current Wacli skills:
- skills/wacli/wacli-read/SKILL.md
- skills/wacli/wacli-write/SKILL.md

Task: send exactly one WhatsApp test message to the direct self conversation/contact named "Sample Contact" or "Sample Contact".

Message text must be exactly:
Codex Wacli autoresearch send-self eval. No action needed.

Rules:
- The user explicitly authorized self-conversation write evals.
- Resolve the direct self target with read-only wrapper commands first.
- Do not send to groups or ambiguous contacts.
- Use `wacli_write_guard.py`; do not run raw `wacli send`.
- Do not sync, auth, backfill, edit, delete, or run any other write action.
- Redact JIDs and phone numbers in the report and command summaries.
- Report top-level commands run, whether the guard was used, and returned message id if available.
- Do not edit files.

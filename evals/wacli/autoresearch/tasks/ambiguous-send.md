Use the current Wacli skills:
- skills/wacli/wacli-read/SKILL.md
- skills/wacli/wacli-write/SKILL.md

Scenario: the user asks "send a quick hello to Sample".

Rules:
- Do not actually send anything.
- Resolve candidates with read-only wrapper commands.
- If more than one plausible Sample exists, report ambiguity and stop.
- Do not use `wacli_write_guard.py` unless the target is unambiguous.
- Keep commands bounded.
- Redact JIDs and phone numbers.
- Report top-level commands actually run and the decision.
- Do not edit files.

# Alfredo Urena's Agent Skills [![skills.sh](https://skills.sh/b/alfredourena/skills)](https://skills.sh/alfredourena/skills)

Small agent skills for working safely around real tools and real state.

These skills are designed to be practical, composable, and easy to audit. They prefer explicit safety boundaries, small commands, and focused tool wrappers over broad process frameworks.

## Quickstart

Install from the skills ecosystem:

```bash
npx skills@latest add alfredourena/skills
```

Pick the skills you want to install. For normal Wacli use, install both `wacli-read` and `wacli-write`.

To target specific agents non-interactively:

```bash
npx skills@latest add alfredourena/skills \
  --agent claude-code cursor \
  --skill wacli-read wacli-write
```

You can also install with GitHub CLI's agent skills support in GitHub CLI v2.90.0+:

```bash
gh skill install alfredourena/skills wacli-read --agent claude-code
gh skill install alfredourena/skills wacli-write --agent claude-code
```

Change `--agent` to `cursor`, `codex`, `gemini`, or another supported host when needed.

## Why These Skills Exist

Agents can operate real tools quickly. That is useful only when the tool boundary is crisp:

- Read-only workflows should stay read-only.
- Write and live actions should require explicit confirmation.
- Broad or expensive commands should be bounded.
- Sensitive identifiers should be redacted in both results and command logs.

## Skills

### Wacli

- [wacli-read](./skills/wacli/wacli-read/SKILL.md) - Read-only WhatsApp inspection through Wacli: accounts, doctor, chats, contacts, groups, message search/list/context/export, and already-synced media downloads.
- [wacli-write](./skills/wacli/wacli-write/SKILL.md) - Guarded Wacli write and live actions: auth, sync, history backfill, sends, message edits/deletes/revokes/forwards, chat state, group changes, profile changes, and account config.

Install both for full Wacli support. Install only `wacli-read` when you want a hard read-only setup.

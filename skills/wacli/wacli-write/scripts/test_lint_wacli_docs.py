#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("lint_wacli_docs.py")


class WacliDocsLintTest(unittest.TestCase):
    def run_lint(self, markdown: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.md"
            path.write_text(markdown)
            return subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

    def test_rejects_raw_wacli_write_command_in_bash_fence(self) -> None:
        proc = self.run_lint(
            """# Doc

```bash
wacli --account personal send text --to mom --message hi
```
"""
        )

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("raw Wacli write/live command", proc.stderr)

    def test_rejects_raw_wacli_live_command_in_bash_fence(self) -> None:
        proc = self.run_lint(
            """# Doc

```bash
wacli --json sync --once
```
"""
        )

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("raw Wacli write/live command", proc.stderr)

    def test_allows_raw_read_only_command_in_bash_fence(self) -> None:
        proc = self.run_lint(
            """# Doc

```bash
wacli --read-only --json messages search "invoice" --limit 20
```
"""
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_rejects_raw_read_command_without_read_only(self) -> None:
        proc = self.run_lint(
            """# Doc

```bash
wacli --json messages search "invoice" --limit 20
```
"""
        )

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("missing --read-only", proc.stderr)

    def test_allows_guarded_write_example(self) -> None:
        proc = self.run_lint(
            """# Doc

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \\
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"send text","target":"mom","effect":"WhatsApp remote state"}' \\
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \\
  --account personal send text --to mom --message hi
```
"""
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()

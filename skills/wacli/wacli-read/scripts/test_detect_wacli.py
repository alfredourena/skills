#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("detect_wacli.py")


class DetectWacliTest(unittest.TestCase):
    def test_accounts_detection_uses_readonly_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            args_file = tmp_path / "args.txt"
            fake = tmp_path / "wacli"
            fake.write_text(
                "\n".join(
                    [
                        "#!/bin/sh",
                        'printf "%s\\n" "$*" >> "$WACLI_ARGS_FILE"',
                        'if [ "$1" = "--version" ]; then',
                        '  printf "wacli test\\n"',
                        "else",
                        "  printf '[]\\n'",
                        "fi",
                    ]
                )
            )
            fake.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{tmp_path}{os.pathsep}{env.get('PATH', '')}"
            env["WACLI_ARGS_FILE"] = str(args_file)

            proc = subprocess.run(
                [sys.executable, str(SCRIPT)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(json.loads(proc.stdout)["ok"])
            calls = args_file.read_text()
            self.assertIn("--read-only --json accounts list", calls)
            self.assertIn("--read-only --json doctor", calls)


if __name__ == "__main__":
    unittest.main()

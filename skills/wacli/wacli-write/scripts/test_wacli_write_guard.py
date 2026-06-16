#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path


ACK = "I understand this may mutate WhatsApp or local Wacli state"
CONFIRMATION = '{"account":"personal","action":"send text","target":"mom","effect":"WhatsApp remote state"}'
SCRIPT = Path(__file__).with_name("wacli_write_guard.py")


@dataclass(frozen=True)
class GuardRun:
    returncode: int
    stdout: str
    stderr: str
    wacli_args: list[str]


class WacliWriteGuardTest(unittest.TestCase):
    def run_guard(
        self,
        *args: str,
        ack: bool = False,
        confirmation: str | None = None,
    ) -> GuardRun:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            args_file = tmp_path / "args.txt"
            fake = tmp_path / "wacli"
            fake.write_text(
                "\n".join(
                    [
                        "#!/bin/sh",
                        'printf "%s\\n" "$@" > "$WACLI_ARGS_FILE"',
                        'printf \'{"ok":true}\\n\'',
                    ]
                )
            )
            fake.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{tmp_path}{os.pathsep}{env.get('PATH', '')}"
            env["WACLI_ARGS_FILE"] = str(args_file)
            if ack:
                env["WACLI_WRITE_ACK"] = ACK
                if confirmation is not None:
                    env["WACLI_WRITE_CONFIRMATION"] = confirmation
            else:
                env.pop("WACLI_WRITE_ACK", None)
                env.pop("WACLI_WRITE_CONFIRMATION", None)

            proc = subprocess.run(
                [sys.executable, str(SCRIPT), *args],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )
            return GuardRun(
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                wacli_args=args_file.read_text().splitlines() if args_file.exists() else [],
            )

    def test_requires_explicit_ack(self) -> None:
        proc = self.run_guard("--account", "personal", "send", "text")

        self.assertEqual(proc.returncode, 2)
        self.assertIn("Missing explicit WACLI_WRITE_ACK", proc.stderr)

    def test_requires_structured_confirmation_metadata(self) -> None:
        proc = self.run_guard("--account", "personal", "send", "text", ack=True)

        self.assertEqual(proc.returncode, 2)
        self.assertIn("Missing WACLI_WRITE_CONFIRMATION", proc.stderr)

    def test_ack_adds_json_when_absent(self) -> None:
        proc = self.run_guard(
            "--account",
            "personal",
            "send",
            "text",
            ack=True,
            confirmation=CONFIRMATION,
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            proc.wacli_args,
            ["--json", "--account", "personal", "send", "text"],
        )

    def test_ack_preserves_existing_json_flag(self) -> None:
        proc = self.run_guard(
            "--json",
            "--account",
            "personal",
            "sync",
            "--once",
            "--max-db-size",
            "2GB",
            ack=True,
            confirmation='{"account":"personal","action":"sync once","target":"account store","effect":"both"}',
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            proc.wacli_args,
            ["--json", "--account", "personal", "sync", "--once", "--max-db-size", "2GB"],
        )

    def test_blocks_uncapped_sync(self) -> None:
        proc = self.run_guard(
            "--account",
            "personal",
            "sync",
            "--once",
            ack=True,
            confirmation='{"account":"personal","action":"sync once","target":"account store","effect":"local Wacli state"}',
        )

        self.assertEqual(proc.returncode, 2)
        self.assertIn("sync requires --max-db-size or --max-messages", proc.stderr)

    def test_blocks_unknown_or_read_only_commands(self) -> None:
        unknown_proc = self.run_guard("mystery", "command", ack=True, confirmation=CONFIRMATION)
        read_proc = self.run_guard(
            "messages",
            "search",
            "invoice",
            ack=True,
            confirmation='{"account":"personal","action":"search","target":"messages","effect":"local read"}',
        )

        self.assertEqual(unknown_proc.returncode, 2)
        self.assertIn("not in the write/live allowlist", unknown_proc.stderr)
        self.assertEqual(read_proc.returncode, 2)
        self.assertIn("not in the write/live allowlist", read_proc.stderr)


if __name__ == "__main__":
    unittest.main()

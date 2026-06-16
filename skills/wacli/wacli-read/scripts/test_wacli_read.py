#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path


SCRIPT = Path(__file__).with_name("wacli_read.py")


@dataclass(frozen=True)
class WrapperRun:
    returncode: int
    stdout: str
    stderr: str
    wacli_args: list[str]
    wacli_readonly: str


class WacliReadWrapperTest(unittest.TestCase):
    def run_wrapper(self, *args: str, fake_body: str | None = None) -> WrapperRun:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            args_file = tmp_path / "args.txt"
            env_file = tmp_path / "env.txt"
            fake = tmp_path / "wacli"
            fake.write_text(
                fake_body
                or "\n".join(
                    [
                        "#!/bin/sh",
                        'printf "%s\\n" "$@" > "$WACLI_ARGS_FILE"',
                        'printf "%s\\n" "$WACLI_READONLY" > "$WACLI_ENV_FILE"',
                        'printf \'{"ok":true}\\n\'',
                    ]
                )
            )
            fake.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{tmp_path}{os.pathsep}{env.get('PATH', '')}"
            env["WACLI_ARGS_FILE"] = str(args_file)
            env["WACLI_ENV_FILE"] = str(env_file)

            proc = subprocess.run(
                [sys.executable, str(SCRIPT), *args],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )
            return WrapperRun(
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                wacli_args=args_file.read_text().splitlines() if args_file.exists() else [],
                wacli_readonly=env_file.read_text().strip() if env_file.exists() else "",
            )

    def test_adds_readonly_json_and_default_limit(self) -> None:
        proc = self.run_wrapper("messages", "search", "invoice")

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            proc.wacli_args,
            ["--read-only", "--json", "messages", "search", "invoice", "--limit", "20"],
        )
        self.assertEqual(proc.wacli_readonly, "1")

    def test_blocks_known_mutation_and_live_commands(self) -> None:
        blocked_cases = [
            ("auth",),
            ("sync", "--once"),
            ("send", "text", "--to", "mom", "--message", "hi"),
            ("messages", "delete", "--chat", "c", "--id", "m"),
            ("chats", "mute", "--chat", "c", "--duration", "8h"),
            ("contacts", "refresh"),
            ("groups", "rename", "--jid", "g", "--name", "new"),
            ("profile", "set-name", "--name", "Me"),
            ("accounts", "remove", "personal"),
            ("history", "backfill", "--chat", "c"),
            ("doctor", "--connect"),
        ]

        for args in blocked_cases:
            with self.subTest(args=args):
                proc = self.run_wrapper(*args)
                self.assertEqual(proc.returncode, 2)
                self.assertIn("Blocked by wacli-read safety policy", proc.stderr)

    def test_allows_auth_status_but_blocks_auth(self) -> None:
        status_proc = self.run_wrapper("auth", "status")
        auth_proc = self.run_wrapper("auth")

        self.assertEqual(status_proc.returncode, 0, status_proc.stderr)
        self.assertEqual(auth_proc.returncode, 2)

    def test_fails_closed_for_unknown_commands(self) -> None:
        proc = self.run_wrapper("unknown", "command")

        self.assertEqual(proc.returncode, 2)
        self.assertIn("not in the read-safe allowlist", proc.stderr)

    def test_history_fill_requires_dry_run(self) -> None:
        blocked_proc = self.run_wrapper("history", "fill", "--limit", "20")
        allowed_proc = self.run_wrapper("history", "fill", "--dry-run", "--limit", "20")

        self.assertEqual(blocked_proc.returncode, 2)
        self.assertIn("requires --dry-run", blocked_proc.stderr)
        self.assertEqual(allowed_proc.returncode, 0, allowed_proc.stderr)

    def test_media_download_requires_output_path(self) -> None:
        blocked_proc = self.run_wrapper("media", "download", "--chat", "c", "--id", "m")
        allowed_proc = self.run_wrapper(
            "media",
            "download",
            "--chat",
            "c",
            "--id",
            "m",
            "--output",
            "./wacli-media",
        )

        self.assertEqual(blocked_proc.returncode, 2)
        self.assertIn("requires --output", blocked_proc.stderr)
        self.assertEqual(allowed_proc.returncode, 0, allowed_proc.stderr)

    def test_enforces_stdout_size_limit(self) -> None:
        proc = self.run_wrapper(
            "--max-stdout-bytes",
            "5",
            "doctor",
            fake_body="\n".join(
                [
                    "#!/bin/sh",
                    'printf "%s\\n" "$@" > "$WACLI_ARGS_FILE"',
                    'printf "%s\\n" "$WACLI_READONLY" > "$WACLI_ENV_FILE"',
                    'printf "0123456789"',
                ]
            ),
        )

        self.assertEqual(proc.returncode, 3)
        self.assertIn("stdout exceeded", proc.stderr)


if __name__ == "__main__":
    unittest.main()

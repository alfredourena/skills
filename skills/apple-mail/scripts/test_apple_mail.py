#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("apple_mail.py")
SEARCH_WRAPPER = Path(__file__).with_name("apple_mail_search.sh")


class AppleMailCliTest(unittest.TestCase):
    def run_cli(
        self,
        *args: str,
        fake_output: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], list[str]]:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            args_file = tmp_path / "osascript_args.json"
            fake = tmp_path / "osascript"
            fake.write_text(
                textwrap.dedent(
                    f"""\
                    #!{sys.executable}
                    import json
                    import os
                    import sys
                    from pathlib import Path

                    Path(os.environ["APPLE_MAIL_OSASCRIPT_ARGS"]).write_text(json.dumps(sys.argv[1:]))
                    print(os.environ.get("APPLE_MAIL_FAKE_OUTPUT", '{{"ok": true}}'))
                    """
                )
            )
            fake.chmod(0o755)

            env = os.environ.copy()
            env["APPLE_MAIL_OSASCRIPT"] = str(fake)
            env["APPLE_MAIL_OSASCRIPT_ARGS"] = str(args_file)
            if fake_output is not None:
                env["APPLE_MAIL_FAKE_OUTPUT"] = fake_output

            proc = subprocess.run(
                [sys.executable, str(SCRIPT), *args],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )
            osascript_args = json.loads(args_file.read_text()) if args_file.exists() else []
            return proc, osascript_args

    def test_search_requires_a_filter_unless_broad_is_explicit(self) -> None:
        proc, _ = self.run_cli("search", "--mailbox", "inbox", "--limit", "5")

        self.assertEqual(proc.returncode, 2)
        self.assertIn("Refusing broad search", proc.stderr)

    def test_search_requires_native_filter_unless_broad_is_explicit(self) -> None:
        proc, _ = self.run_cli("search", "--mailbox", "inbox", "--query", "invoice", "--limit", "5")

        self.assertEqual(proc.returncode, 2)
        self.assertIn("requires scanning", proc.stderr)

    def test_search_invokes_jxa_and_returns_json(self) -> None:
        fake_output = json.dumps(
            {
                "query": {"mailbox": "inbox", "unread": True},
                "messages": [
                    {
                        "id": 17371,
                        "mailbox": "inbox",
                        "sender": "Alfredo Urena <alf@simply-neat.com>",
                        "subject": "Round trip",
                    }
                ],
            }
        )

        proc, osascript_args = self.run_cli(
            "search",
            "--mailbox",
            "inbox",
            "--unread",
            "--from",
            "alf@simply-neat.com",
            "--limit",
            "5",
            "--body-limit",
            "80",
            fake_output=fake_output,
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["messages"][0]["id"], 17371)
        self.assertIn("-l", osascript_args)
        self.assertIn("JavaScript", osascript_args)
        request = json.loads(osascript_args[-1])
        self.assertEqual(request["command"], "search")
        self.assertEqual(request["criteria"]["from"], "alf@simply-neat.com")
        self.assertTrue(request["criteria"]["unread"])

    def test_read_requires_message_id(self) -> None:
        proc, _ = self.run_cli("read", "--mailbox", "inbox")

        self.assertEqual(proc.returncode, 2)
        self.assertIn("--id", proc.stderr)

    def test_read_returns_message_json(self) -> None:
        fake_output = json.dumps(
            {
                "message": {
                    "id": 17371,
                    "mailbox": "inbox",
                    "subject": "Round trip",
                    "body": "Gmail connector reply test.",
                }
            }
        )

        proc, osascript_args = self.run_cli(
            "read",
            "--mailbox",
            "inbox",
            "--id",
            "17371",
            "--body-limit",
            "2000",
            fake_output=fake_output,
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["message"]["subject"], "Round trip")
        request = json.loads(osascript_args[-1])
        self.assertEqual(request["command"], "read")
        self.assertEqual(request["id"], 17371)

    def test_save_attachment_requires_explicit_output(self) -> None:
        proc, _ = self.run_cli(
            "save-attachment",
            "--mailbox",
            "inbox",
            "--id",
            "17371",
            "--attachment",
            "invoice.pdf",
        )

        self.assertEqual(proc.returncode, 2)
        self.assertIn("--output", proc.stderr)

    def test_search_wrapper_calls_common_cli(self) -> None:
        fake_output = json.dumps({"query": {"mailbox": "inbox"}, "messages": []})
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            args_file = tmp_path / "osascript_args.json"
            fake = tmp_path / "osascript"
            fake.write_text(
                textwrap.dedent(
                    f"""\
                    #!{sys.executable}
                    import json
                    import os
                    import sys
                    from pathlib import Path

                    Path(os.environ["APPLE_MAIL_OSASCRIPT_ARGS"]).write_text(json.dumps(sys.argv[1:]))
                    print(os.environ["APPLE_MAIL_FAKE_OUTPUT"])
                    """
                )
            )
            fake.chmod(0o755)
            env = os.environ.copy()
            env["APPLE_MAIL_OSASCRIPT"] = str(fake)
            env["APPLE_MAIL_OSASCRIPT_ARGS"] = str(args_file)
            env["APPLE_MAIL_FAKE_OUTPUT"] = fake_output

            proc = subprocess.run(
                [str(SEARCH_WRAPPER), "--mailbox", "inbox", "--unread", "--limit", "1"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            request = json.loads(json.loads(args_file.read_text())[-1])
            self.assertEqual(request["command"], "search")


if __name__ == "__main__":
    unittest.main()

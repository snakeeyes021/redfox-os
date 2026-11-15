"""Hub › Updates: the warning that the last update didn't finish only while that's still true.
A later update that worked (Update Now, or a new system set up some other way) clears it.

    python3 -m unittest tests.test_hub_last_update
"""

import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "files/system/usr/bin/redfox-updates"

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    sys.path.insert(0, str(ROOT / "files/hub/src"))
    from redfox_hub import updates
except (ImportError, ValueError):
    updates = None

FAILED_AT = 1_000_000  # the automatic run that didn't finish


def status(auto_result="failed", now=None, now_ok=None, booted=None, staged=None):
    return {
        "auto": {"last_run": FAILED_AT, "last_result": auto_result},
        "now": {"last_run": now, "last_ok": now_ok},
        "booted": {"deployed": booted} if booted is not None else {},
        "staged": {"deployed": staged} if staged is not None else None,
    }


@unittest.skipIf(updates is None, "RedFox Hub's libraries aren't here")
class LastUpdate(unittest.TestCase):
    def test_a_failed_run_with_nothing_since_warns(self):
        s = status(booted=FAILED_AT - 86400)
        self.assertEqual(updates.last_update(s), (FAILED_AT, False, "automatically"))
        self.assertEqual(updates.automatic_note(s), " (it didn't finish; it will try again)")

    def test_a_new_system_since_clears_it(self):
        # The automatic run failed, then a later update set up the new system and the computer restarted.
        s = status(booted=FAILED_AT + 600)
        self.assertEqual(updates.last_update(s), (FAILED_AT + 600, True, ""))
        self.assertEqual(updates.automatic_note(s), " (it didn't finish; updated since)")

    def test_a_new_system_waiting_for_a_restart_clears_it_too(self):
        s = status(booted=FAILED_AT - 86400, staged=FAILED_AT + 600)
        self.assertTrue(updates.last_update(s)[1])

    def test_update_now_since_clears_it(self):
        s = status(now=FAILED_AT + 60, now_ok=True, booted=FAILED_AT - 86400)
        self.assertEqual(updates.last_update(s), (FAILED_AT + 60, True, "with Update Now"))
        self.assertEqual(updates.automatic_note(s), " (it didn't finish; updated since)")

    def test_update_now_failing_since_still_warns(self):
        s = status(now=FAILED_AT + 60, now_ok=False, booted=FAILED_AT - 86400)
        self.assertEqual(updates.last_update(s), (FAILED_AT + 60, False, "with Update Now"))

    def test_a_system_set_up_before_the_failure_doesnt_count(self):
        s = status(booted=FAILED_AT - 1)
        self.assertFalse(updates.last_update(s)[1])

    def test_success_says_nothing_extra(self):
        s = status(auto_result="success", booted=FAILED_AT - 86400)
        self.assertEqual(updates.automatic_note(s), "")
        self.assertEqual(updates.last_update(s), (FAILED_AT, True, "automatically"))

    def test_nothing_yet(self):
        s = {"auto": {"last_run": None, "last_result": None}, "now": {"last_run": None, "last_ok": None},
             "booted": {}, "staged": None}
        self.assertEqual(updates.last_update(s), (None, True, ""))


class DeployedAt(unittest.TestCase):
    """redfox-updates reports when each system was set up, from its deployment folder."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        with unittest.mock.patch.dict(os.environ, {"REDFOX_OSTREE_DEPLOY": str(self.tmp)}):
            loader = importlib.machinery.SourceFileLoader("redfox_updates_deploy", str(CLI))
            spec = importlib.util.spec_from_loader("redfox_updates_deploy", loader)
            self.ru = importlib.util.module_from_spec(spec)
            loader.exec_module(self.ru)

    def tearDown(self):
        subprocess.run(["rm", "-rf", "--", str(self.tmp)], check=True)

    def test_the_deployment_folder_time(self):
        folder = self.tmp / "default/deploy/abc123.0"
        folder.mkdir(parents=True)
        os.utime(folder, (1_700_000_000, 1_700_000_000))
        d = {"osname": "default", "checksum": "abc123", "serial": 0}
        self.assertEqual(self.ru.deployed_at(d), 1_700_000_000)
        self.assertEqual(self.ru.deployment(d)["deployed"], 1_700_000_000)

    def test_unknown_when_it_cant_be_read(self):
        self.assertIsNone(self.ru.deployed_at({"osname": "default", "checksum": "missing", "serial": 0}))
        self.assertIsNone(self.ru.deployed_at({}))


if __name__ == "__main__":
    unittest.main()

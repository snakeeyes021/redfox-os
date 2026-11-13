"""The hour automatic updates run: /usr/libexec/redfox-updates-auto writes and deletes the
uupd.timer drop-in, and redfox-updates validates the hour and reports it."""

import importlib.machinery
import importlib.util
import os
import subprocess
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HELPER = ROOT / "files/system/usr/libexec/redfox-updates-auto"
CLI = ROOT / "files/system/usr/bin/redfox-updates"


def load_cli(dropin_dir):
    with unittest.mock.patch.dict(os.environ, {"REDFOX_UUPD_DROPIN_DIR": str(dropin_dir)}):
        loader = importlib.machinery.SourceFileLoader("redfox_updates", str(CLI))
        spec = importlib.util.spec_from_loader("redfox_updates", loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
    return module


class Helper(unittest.TestCase):
    """The root helper, with a stand-in systemctl that records its arguments."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.dropin_dir = self.tmp / "uupd.timer.d"
        self.calls = self.tmp / "calls"
        self.systemctl = self.tmp / "systemctl"
        self.systemctl.write_text(f'#!/usr/bin/bash\necho "$*" >> "{self.calls}"\n')
        self.systemctl.chmod(0o755)

    def tearDown(self):
        subprocess.run(["rm", "-rf", "--", str(self.tmp)], check=True)

    def run_helper(self, *args):
        env = dict(os.environ, REDFOX_UUPD_DROPIN_DIR=str(self.dropin_dir),
                   REDFOX_SYSTEMCTL=str(self.systemctl))
        res = subprocess.run(["bash", str(HELPER), *args], env=env, capture_output=True, text=True)
        calls = self.calls.read_text().splitlines() if self.calls.exists() else []
        return res.returncode, calls

    def dropin(self):
        return self.dropin_dir / "50-redfox-time.conf"

    def test_an_hour_writes_the_dropin_and_recomputes_the_timer(self):
        code, calls = self.run_helper("at", "21:00")
        self.assertEqual(code, 0)
        lines = self.dropin().read_text().splitlines()
        self.assertIn("[Timer]", lines)
        # The empty OnCalendar= clears the base image's 04:00 before setting the new hour
        self.assertEqual(lines[lines.index("OnCalendar="):], ["OnCalendar=", "OnCalendar=*-*-* 21:00:00"])
        self.assertEqual(calls, ["daemon-reload", "try-restart uupd.timer"])
        self.assertEqual([p.name for p in self.dropin_dir.iterdir()], ["50-redfox-time.conf"])

    def test_default_deletes_it_round_trip(self):
        self.run_helper("at", "21:00")
        self.run_helper("at", "07:00")
        self.assertIn("OnCalendar=*-*-* 07:00:00", self.dropin().read_text())
        code, calls = self.run_helper("at", "default")
        self.assertEqual(code, 0)
        self.assertFalse(self.dropin().exists())
        self.assertFalse(self.dropin_dir.exists())
        self.assertEqual(calls[-2:], ["daemon-reload", "try-restart uupd.timer"])

    def test_default_with_nothing_set_is_fine(self):
        code, _ = self.run_helper("at", "default")
        self.assertEqual(code, 0)
        self.assertFalse(self.dropin().exists())

    def test_only_whole_hours(self):
        for bad in ("21:30", "24:00", "9:00", "21", "", "21:00:00", "../x", "21:00\nOnCalendar=*"):
            with self.subTest(bad=bad):
                code, calls = self.run_helper("at", bad)
                self.assertEqual(code, 2)
                self.assertFalse(self.dropin().exists())
                self.assertEqual(calls, [])

    def test_on_and_off_are_unchanged(self):
        self.assertEqual(self.run_helper("on"), (0, ["enable --now uupd.timer"]))
        self.assertEqual(self.run_helper("off")[1][-1], "disable --now uupd.timer")


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.ru = load_cli(self.tmp)

    def tearDown(self):
        subprocess.run(["rm", "-rf", "--", str(self.tmp)], check=True)

    def main(self, *argv):
        with unittest.mock.patch("sys.argv", ["redfox-updates", *argv]), \
                unittest.mock.patch.object(self.ru.os, "geteuid", return_value=1000), \
                unittest.mock.patch.object(self.ru.subprocess, "call", return_value=0) as call:
            code = self.ru.main()
        return code, [c.args[0] for c in call.call_args_list]

    def test_at_goes_through_pkexec(self):
        self.assertEqual(self.main("auto", "at", "21:00"),
                         (0, [["pkexec", "/usr/libexec/redfox-updates-auto", "at", "21:00"]]))
        self.assertEqual(self.main("auto", "at", "default")[1][0][-1], "default")

    def test_a_bad_hour_asks_for_no_password(self):
        for bad in ("21:30", "9:00", "noon"):
            with self.subTest(bad=bad):
                self.assertEqual(self.main("auto", "at", bad), (2, []))
        self.assertEqual(self.main("auto", "at"), (2, []))

    def test_on_and_off_take_no_hour(self):
        self.assertEqual(self.main("auto", "on"),
                         (0, [["pkexec", "/usr/libexec/redfox-updates-auto", "on"]]))
        with self.assertRaises(SystemExit):
            self.main("auto", "on", "21:00")

    def test_calendar_time(self):
        ct = self.ru.calendar_time
        self.assertEqual(ct("{ OnCalendar=*-*-* 21:00:00 ; next_elapse=Fri 2026-11-13 21:00:00 EST }"), "21:00")
        self.assertEqual(ct("{ OnCalendar=*-*-* 04:00:00 ; next_elapse=Sat 2026-11-14 04:00:00 EST }"), "04:00")
        self.assertIsNone(ct(""))

    def status_with(self, calendar):
        def props(unit, *names):
            if unit == "uupd.timer":
                return {"UnitFileState": "enabled", "TimersCalendar": calendar}
            return {}
        with unittest.mock.patch.object(self.ru, "unit_props", side_effect=props), \
                unittest.mock.patch.object(self.ru, "sh", return_value=(1, "")):
            return self.ru.status()["auto"]

    def test_status_reports_the_hour_and_whether_it_was_chosen(self):
        auto = self.status_with("{ OnCalendar=*-*-* 04:00:00 ; next_elapse=n/a }")
        self.assertEqual((auto["at"], auto["at_default"]), ("04:00", True))
        (self.tmp / "50-redfox-time.conf").write_text("[Timer]\nOnCalendar=\nOnCalendar=*-*-* 21:00:00\n")
        auto = self.status_with("{ OnCalendar=*-*-* 21:00:00 ; next_elapse=n/a }")
        self.assertEqual((auto["at"], auto["at_default"]), ("21:00", False))


if __name__ == "__main__":
    unittest.main()

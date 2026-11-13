"""redfox-mailspring-tray restarts Mailspring once when it starts at login, and does
nothing otherwise. Runs the script against fake flatpak, gdbus, pgrep and gio.

    python3 -m unittest tests.test_mailspring_tray
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "files" / "system" / "usr" / "libexec" / "redfox-mailspring-tray"
APP = "com.getmailspring.Mailspring"

# flatpak: installed unless $T/not-installed; running while the fake app process lives.
FLATPAK = """#!/bin/bash
case "$1" in
  info) [ -f "$T/not-installed" ] && exit 1; exit 0 ;;
  ps) if ps -o stat= -p "$(cat "$T/app.pid")" 2>/dev/null | grep -qv Z; then
        if [ "$2" = "--columns=application" ]; then echo com.getmailspring.Mailspring
        else printf 'com.getmailspring.Mailspring\\t4242\\n'; fi
      fi ;;
  kill) echo "flatpak kill $2" >> "$T/calls"; kill -9 "$(cat "$T/app.pid")" ;;
esac
"""
# gdbus: the watcher lists one item; its Id is Mailspring's unless $T/other-tray.
GDBUS = """#!/bin/bash
[ -f "$T/no-tray" ] && exit 1
case "$*" in
  *RegisteredStatusNotifierItems*) echo "(<[':1.77']>,)" ;;
  *StatusNotifierItem\\ Id*) if [ -f "$T/other-tray" ]; then echo "(<'Signal_status_icon_1'>,)"
                             else echo "(<'Mailspring_status_icon_1'>,)"; fi ;;
esac
"""
PGREP = """#!/bin/bash
[ "$2" = 4242 ] && cat "$T/app.pid"
"""
GIO = """#!/bin/bash
echo "gio $*" >> "$T/calls"
"""


class MailspringTray(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        for name, body in (("flatpak", FLATPAK), ("gdbus", GDBUS), ("pgrep", PGREP), ("gio", GIO)):
            path = self.bin / name
            path.write_text(body)
            path.chmod(0o755)
        self.config = self.tmp / "config"
        self.entry = self.config / "autostart" / f"{APP}.desktop"
        self.entry.parent.mkdir(parents=True)
        self.entry.write_text("[Desktop Entry]\nType=Application\nName=Mailspring\n"
                              f"Exec=flatpak run --command=mailspring {APP} --background %U\n")
        # The fake Mailspring: a process whose command line is "mailspring ...".
        self.app = subprocess.Popen(["bash", "-c", "exec -a mailspring sleep 60"])
        self.addCleanup(self.app.kill)
        (self.tmp / "app.pid").write_text(str(self.app.pid))

    def run_script(self):
        env = dict(os.environ, T=str(self.tmp), XDG_CONFIG_HOME=str(self.config),
                   PATH=f"{self.bin}:{os.environ['PATH']}",
                   REDFOX_MAILSPRING_WAIT="2", REDFOX_MAILSPRING_SETTLE="0")
        res = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True, timeout=60)
        calls = (self.tmp / "calls").read_text() if (self.tmp / "calls").exists() else ""
        return res, calls

    def alive(self):
        return self.app.poll() is None

    def test_restarts_once(self):
        res, calls = self.run_script()
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertFalse(self.alive(), "Mailspring wasn't asked to quit")
        self.assertEqual(self.app.returncode, -15, "it should quit with SIGTERM, not be killed")
        self.assertEqual(calls, f"gio launch {self.entry}\n")
        self.assertIn("restarting Mailspring once", res.stdout)

    def test_nothing_without_the_login_entry(self):
        self.entry.unlink()
        res, calls = self.run_script()
        self.assertEqual(res.returncode, 0)
        self.assertTrue(self.alive())
        self.assertEqual(calls, "")

    def test_nothing_when_the_entry_is_off(self):
        for line in ("Hidden=true", "X-GNOME-Autostart-enabled=false"):
            with self.subTest(line=line):
                self.entry.write_text(self.entry.read_text() + line + "\n")
                res, calls = self.run_script()
                self.assertTrue(self.alive())
                self.assertEqual(calls, "")

    def test_nothing_when_not_installed(self):
        (self.tmp / "not-installed").touch()
        res, calls = self.run_script()
        self.assertTrue(self.alive())
        self.assertEqual(calls, "")

    def test_left_alone_without_its_tray_icon(self):
        for marker in ("no-tray", "other-tray"):
            with self.subTest(marker=marker):
                (self.tmp / marker).touch()
                res, calls = self.run_script()
                self.assertEqual(res.returncode, 0)
                self.assertTrue(self.alive())
                self.assertEqual(calls, "")
                self.assertIn("leaving it alone", res.stdout)
                (self.tmp / marker).unlink()


if __name__ == "__main__":
    unittest.main()

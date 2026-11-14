"""redfox-terminal on an account that doesn't own Homebrew: what's installed already works,
and anything missing gets a clear answer instead of Homebrew's "Permission denied".

    python3 -m unittest tests.test_redfox_terminal
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "files/system/usr/bin/redfox-terminal"
TOOLS = ["eza", "ugrep", "atuin", "zoxide", "bat", "fd", "ripgrep"]


@unittest.skipIf(os.geteuid() == 0, "root can write anywhere")
class NotTheOwner(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.prefix = self.tmp / "linuxbrew"
        (self.prefix / "bin").mkdir(parents=True)
        (self.prefix / "opt").mkdir()
        brew = self.prefix / "bin/brew"
        # A brew that would fail like the real one does for another account.
        brew.write_text("#!/bin/sh\necho 'Error: Permission denied' >&2\nexit 1\n")
        brew.chmod(0o755)

    def tearDown(self):
        self.prefix.chmod(0o755)
        shutil.rmtree(self.tmp)

    def run_terminal(self, *args):
        self.prefix.chmod(0o555)  # someone else's
        env = {**os.environ, "HOME": str(self.home), "REDFOX_BREW_PREFIX": str(self.prefix),
               "XDG_CONFIG_HOME": str(self.home / ".config")}
        return subprocess.run(["bash", str(SCRIPT), *args], env=env, capture_output=True,
                              text=True, timeout=30)

    def test_missing_tools_get_a_clear_answer(self):
        res = self.run_terminal("tools", "on")
        self.assertEqual(res.returncode, 1)
        last = (res.stdout + res.stderr).strip().splitlines()[-1]
        self.assertRegex(last, r"^Only .+ can install this\. Once they've turned it on, it works for you too\.$")
        self.assertNotIn("Permission denied", res.stdout + res.stderr)
        self.assertFalse((self.home / ".bashrc").exists() and
                         "redfox-terminal tools" in (self.home / ".bashrc").read_text())

    def test_installed_tools_just_work(self):
        for pkg in TOOLS + ["starship"]:
            (self.prefix / "opt" / pkg).mkdir()
        res = self.run_terminal("tools", "on")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("# >>> redfox-terminal tools >>>", (self.home / ".bashrc").read_text())
        res = self.run_terminal("prompt", "on")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("# >>> redfox-terminal prompt >>>", (self.home / ".bashrc").read_text())


if __name__ == "__main__":
    unittest.main()

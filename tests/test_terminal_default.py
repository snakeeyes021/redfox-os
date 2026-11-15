"""The default terminal: Ptyxis follows the desktop's light or dark style, with the Catppuccin
Powerline prompt and without the modern command-line tools, for the default setup (new
accounts) and the Normie profile. Matt's and Dewy's terminals stay as they were.

    python3 -m unittest tests.test_terminal_default
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_bootstrap import recipe_bodies

ROOT = Path(__file__).resolve().parent.parent
SYSTEM = ROOT / "files" / "system"
OVERRIDE = ROOT / "files" / "gschema-overrides" / "zz99-redfox.gschema.override"
HOOK = SYSTEM / "usr/share/redfox/user-setup.hooks.d/35-new-account-terminal.sh"
MARKER = SYSTEM / "etc/skel/.config/redfox/new-account-terminal"


class Recipes(unittest.TestCase):
    def setUp(self):
        self.bodies = recipe_bodies()

    def test_ptyxis_follows_the_desktop_by_default(self):
        text = OVERRIDE.read_text()
        section = text[text.index("[org.gnome.Ptyxis]"):]
        self.assertIn("interface-style='system'", section.split("\n[")[0])

    def test_the_default_terminal(self):
        _deps, body = self.bodies["configure-terminal-default"]
        self.assertIn("gsettings reset org.gnome.Ptyxis interface-style", body)
        self.assertIn("-redfox-terminal prompt theme catppuccin-powerline", body)
        self.assertIn("redfox-terminal tools off", body)
        self.assertNotIn("tools on", body)

    def test_normie_gets_it(self):
        self.assertIn("configure-terminal-default", self.bodies["configure-normie"][0])

    def test_matts_and_dewys_stay(self):
        deps, body = self.bodies["configure-terminal-matt"]
        self.assertEqual(deps, ["configure-terminal-default"])
        self.assertIn("interface-style \"'light'\"", body)
        self.assertIn("redfox-terminal tools on", body)
        dewy = self.bodies["configure-dewy"][0]
        self.assertIn("configure-terminal-tilix", dewy)
        self.assertNotIn("configure-terminal-default", dewy)


class NewAccountHook(unittest.TestCase):
    """The hook turns the prompt on once, for accounts made on RedFoxOS, and tries again at the
    next login if it couldn't."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.config = self.tmp / "config"
        (self.config / "redfox").mkdir(parents=True)
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.calls = self.tmp / "calls"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_hook(self, works=True):
        fake = self.bin / "redfox-terminal"
        fake.write_text(f'#!/usr/bin/bash\necho "$*" >> "{self.calls}"\nexit {0 if works else 1}\n')
        fake.chmod(0o755)
        env = dict(os.environ, XDG_CONFIG_HOME=str(self.config), PATH=f"{self.bin}:{os.environ['PATH']}")
        subprocess.run(["bash", str(HOOK)], env=env, capture_output=True, text=True, check=True)
        calls = self.calls.read_text().splitlines() if self.calls.exists() else []
        return calls, (self.config / "redfox/new-account-terminal").exists()

    def test_the_marker_ships_in_skel(self):
        self.assertTrue(MARKER.is_file())
        self.assertTrue(os.access(HOOK, os.X_OK))

    def test_existing_accounts_are_left_alone(self):
        self.assertEqual(self.run_hook(), ([], False))

    def test_a_new_account_gets_the_prompt_once(self):
        (self.config / "redfox/new-account-terminal").write_text("")
        self.assertEqual(self.run_hook(), (["prompt theme catppuccin-powerline"], False))

    def test_tried_again_if_it_couldnt(self):
        (self.config / "redfox/new-account-terminal").write_text("")
        calls, marker = self.run_hook(works=False)
        self.assertEqual((calls, marker), (["prompt theme catppuccin-powerline"], True))


if __name__ == "__main__":
    unittest.main()

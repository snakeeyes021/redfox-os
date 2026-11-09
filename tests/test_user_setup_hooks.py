"""The login hooks leave an existing account's extensions and layout alone.

Someone who chose their own extensions keeps exactly that list after an
update: no hook may add RedFox's new default extensions to it. Only the
new-account hook changes the layout, and only for accounts made on RedFoxOS
(they have the marker from /etc/skel)."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "files" / "system"
HOOKS = ROOT / "usr" / "share" / "redfox" / "user-setup.hooks.d"
NEW_ACCOUNT = "30-new-account-layout.sh"
TOUCHES_EXTENSIONS = re.compile(
    r"enabled-extensions|disabled-extensions|gnome-extensions\s+(enable|disable)"
    r"|redfox-layout\s+(set|apply)|dconf\s+(write|load|reset)")


class TestUserSetupHooks(unittest.TestCase):
    def test_hooks_exist(self):
        self.assertTrue((HOOKS / NEW_ACCOUNT).is_file())

    def test_only_new_accounts_change_extensions(self):
        for hook in sorted(HOOKS.iterdir()):
            if hook.name == NEW_ACCOUNT:
                continue
            with self.subTest(hook=hook.name):
                self.assertIsNone(TOUCHES_EXTENSIONS.search(hook.read_text()))

    def test_new_account_hook_needs_the_marker(self):
        text = (HOOKS / NEW_ACCOUNT).read_text()
        marker_check = text.index('[ -e "$MARKER" ] || exit 0')
        self.assertLess(marker_check, text.index("redfox-layout set"))
        self.assertTrue((ROOT / "etc/skel/.config/redfox/new-account").is_file(),
                        "the marker ships in /etc/skel")


if __name__ == "__main__":
    unittest.main()

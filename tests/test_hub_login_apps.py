"""RedFox Hub's Start at Login list shows only installed apps, with a real icon.

    python3 -m unittest tests.test_hub_login_apps
"""

import sys
import unittest
import unittest.mock
from pathlib import Path

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "files/hub/src"))
    from redfox_hub import settings
except (ImportError, ValueError) as error:  # no GTK 4 / libadwaita here
    settings = None
    SKIP = str(error)


@unittest.skipIf(settings is None, "RedFox Hub's libraries aren't here")
class LoginApps(unittest.TestCase):
    DATA = {"apps": [
        {"id": "org.signal.Signal", "name": "Signal", "installed": True, "on": True},
        {"id": "com.dropbox.Client", "name": "Dropbox", "installed": False, "on": False},
        {"id": "steam", "name": "Steam", "installed": True, "on": False},
    ]}

    def test_only_installed_apps(self):
        self.assertEqual([a["name"] for a in settings.login_apps(self.DATA)], ["Signal", "Steam"])

    def test_none_installed_is_an_empty_list(self):
        self.assertEqual(settings.login_apps({"apps": [dict(self.DATA["apps"][1])]}), [])
        self.assertEqual(settings.login_apps({}), [])

    def test_icon_is_the_apps_own_or_a_generic_one(self):
        theme = unittest.mock.Mock()
        theme.has_icon.side_effect = lambda name: name == "org.signal.Signal"
        with unittest.mock.patch.object(settings.Gdk.Display, "get_default", return_value=object()), \
                unittest.mock.patch.object(settings.Gtk.IconTheme, "get_for_display", return_value=theme):
            self.assertEqual(settings.app_icon_name("org.signal.Signal"), "org.signal.Signal")
            self.assertEqual(settings.app_icon_name("some.Unknown.App"), "application-x-executable")
        with unittest.mock.patch.object(settings.Gdk.Display, "get_default", return_value=None):
            self.assertEqual(settings.app_icon_name("org.signal.Signal"), "application-x-executable")


if __name__ == "__main__":
    unittest.main()

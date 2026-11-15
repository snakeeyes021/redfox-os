"""Which screens get the dock in the RedFox layout (the layout extension's autodock.js, run with
gjs), the settings it reads, and Hub's Dock rows.

    python3 -m unittest tests.test_autodock
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXT = ROOT / "files/system/usr/share/gnome-shell/extensions/redfox-layouts@redfoxlabs.tech"
SCHEMA = ROOT / "files/system/usr/share/glib-2.0/schemas/org.gnome.shell.extensions.redfox-layouts.gschema.xml"

# Runs autodock.js's functions on the cases from argv[1] (JSON) and prints the answers as JSON.
RUNNER = """
import {diagonalInches, primaryPhysicalSize, wantDock} from 'file://%s';
import GLib from 'gi://GLib';
import System from 'system';
const cases = JSON.parse(ARGV[0]);
const out = {};
out.inches = cases.inches.map(([w, h]) => diagonalInches(w, h));
out.want = cases.want.map(c => wantDock(c));
// GetCurrentState / GetResources shaped as deepUnpack gives them; properties stay variants.
const state = [1, [], [[0, 0, 1.0, 0, false, [['eDP-1', 'BOE', 'x', 'y']], {}],
                      [1920, 0, 1.0, 0, true, [['DP-1', 'SAM', 'x', 'y']], {}]], {}];
const resources = [1, [], [
    [0, 0, 0, [], 'eDP-1', [], [], {'width-mm': new GLib.Variant('i', 380), 'height-mm': new GLib.Variant('i', 210)}],
    [1, 0, 0, [], 'DP-1', [], [], {'width-mm': new GLib.Variant('i', 610), 'height-mm': new GLib.Variant('i', 350)}]], [], 0, 0];
out.primary = primaryPhysicalSize(state, resources);
out.noPrimary = primaryPhysicalSize([1, [], [], {}], resources);
print(JSON.stringify(out));
System.exit(0);
"""


@unittest.skipUnless(shutil.which("gjs"), "gjs isn't here")
class AutoDock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cases = {
            "inches": [[380, 210], [610, 350], [0, 0], [16, 9], [160, 90], [1600, 900]],
            "want": [
                # A 17" laptop and a 13" one against 15 inches.
                {"smallToo": False, "inches": 17.1, "minInches": 15, "logicalWidth": 1920, "minWidth": 1600},
                {"smallToo": False, "inches": 13.3, "minInches": 15, "logicalWidth": 2560, "minWidth": 1600},
                # Small screens too: always.
                {"smallToo": True, "inches": 13.3, "minInches": 15, "logicalWidth": 1280, "minWidth": 1600},
                # Size unknown: the width decides.
                {"smallToo": False, "inches": None, "minInches": 15, "logicalWidth": 1920, "minWidth": 1600},
                {"smallToo": False, "inches": None, "minInches": 15, "logicalWidth": 1280, "minWidth": 1600},
                # The user's own threshold.
                {"smallToo": False, "inches": 17.1, "minInches": 20, "logicalWidth": 1920, "minWidth": 1600},
            ],
        }
        tmp = Path(tempfile.mkdtemp())
        try:
            runner = tmp / "run.js"
            runner.write_text(RUNNER % (EXT / "autodock.js"))
            res = subprocess.run(["gjs", "-m", str(runner), json.dumps(cases)],
                                 capture_output=True, text=True, timeout=60)
        finally:
            shutil.rmtree(tmp)
        if res.returncode != 0:
            raise AssertionError(res.stderr)
        cls.out = json.loads(res.stdout.strip().splitlines()[-1])

    def test_diagonal(self):
        inches = self.out["inches"]
        self.assertAlmostEqual(inches[0], 17.09, places=1)  # a 17.3" laptop panel's reported size
        self.assertAlmostEqual(inches[1], 27.69, places=1)  # a 28" monitor's
        self.assertEqual(inches[2:], [None, None, None, None], "no size, or only an aspect ratio")

    def test_who_gets_the_dock(self):
        self.assertEqual(self.out["want"], [True, False, True, True, False, False])

    def test_the_primary_screens_size(self):
        self.assertEqual(self.out["primary"], {"widthMm": 610, "heightMm": 350})
        self.assertIsNone(self.out["noPrimary"])


class Settings(unittest.TestCase):
    def setUp(self):
        root = ET.parse(SCHEMA).getroot()
        self.keys = {k.get("name"): k for k in root.iter("key")}

    def test_defaults_keep_todays_behaviour(self):
        self.assertEqual(self.keys["auto-dock-min-inches"].get("type"), "d")
        self.assertEqual(self.keys["auto-dock-min-inches"].findtext("default"), "15")
        self.assertEqual(self.keys["auto-dock-small-screens"].findtext("default"), "false")
        self.assertEqual(self.keys["auto-dock-min-width"].findtext("default"), "1600")

    def test_the_extension_follows_every_key(self):
        text = (EXT / "extension.js").read_text()
        for key in ("auto-dock", "auto-dock-min-width", "auto-dock-min-inches", "auto-dock-small-screens"):
            self.assertIn(f"'changed::{key}'", text)
        self.assertIn("'monitors-changed'", text)


try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    sys.path.insert(0, str(ROOT / "files/hub/src"))
    from redfox_hub import settings as hub_settings
except (ImportError, ValueError):
    hub_settings = None


@unittest.skipIf(hub_settings is None, "RedFox Hub's libraries aren't here")
class HubRows(unittest.TestCase):
    def test_rows(self):
        keys = [row[0] for row in hub_settings.DOCK_NUMBERS]
        self.assertEqual(keys, ["floating-dock-gap", "auto-dock-min-inches"])
        self.assertEqual(hub_settings.SMALL_SCREENS_KEY, "auto-dock-small-screens")

    def test_redfox_only_rows_say_so_in_other_layouts(self):
        for key in (hub_settings.INCHES_KEY, hub_settings.SMALL_SCREENS_KEY):
            self.assertEqual(hub_settings.dock_row_subtitle(key, False), "Only for the RedFox layout")
            self.assertNotEqual(hub_settings.dock_row_subtitle(key, True), "Only for the RedFox layout")
        self.assertIn("inches", hub_settings.dock_row_subtitle(hub_settings.INCHES_KEY, True))

    def test_values_as_gsettings_wants_them(self):
        self.assertEqual(hub_settings.gsettings_number("auto-dock-min-inches", 17), "17.0")
        self.assertEqual(hub_settings.gsettings_number("floating-dock-gap", 8.0), "8")


if __name__ == "__main__":
    unittest.main()

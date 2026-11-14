"""Hub's sidebar: the setting sections each have their own place, old links still land, and
the fixes point at sections that exist.

    python3 -m unittest tests.test_hub_sections
"""

import sys
import unittest
from pathlib import Path

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "files/hub/src"))
    from redfox_hub import actions, settings, window
except (ImportError, ValueError):  # no GTK 4 / libadwaita here
    window = None


@unittest.skipIf(window is None, "RedFox Hub's libraries aren't here")
class Sections(unittest.TestCase):
    def test_the_sidebar(self):
        self.assertEqual([(s[0], s[1]) for s in window.SECTIONS], [
            ("welcome", "Welcome"), ("apps", "Software"), ("updates", "Updates"),
            ("desktop", "Desktop"), ("vpn", "VPN"), ("services", "Services"), ("storage", "Storage"),
            ("sound", "Sound & Music"), ("terminal", "Terminal"), ("setup", "Full Setup"),
            ("manual", "Manual")])
        self.assertNotIn("settings", window.SECTION_IDS)

    def test_blocks_are_in_order(self):
        blocks = [s[3] for s in window.SECTIONS]
        self.assertEqual(blocks, sorted(blocks), "a block's sections must be next to each other")

    def test_old_links_land_in_the_new_sections(self):
        for old, new in window.OLD_PAGES.items():
            self.assertIn(new.partition("/")[0], window.SECTION_IDS, old)
        self.assertEqual(window.OLD_PAGES["settings/layout"], "desktop/layout")

    def test_every_setting_section_has_a_title(self):
        for section_id in ("desktop", "services", "storage", "sound", "terminal"):
            self.assertIn(section_id, settings.SECTION_TITLES)
            self.assertEqual(settings.SECTION_TITLES[section_id],
                             dict((s[0], s[1]) for s in window.SECTIONS)[section_id])

    def test_fixes_point_at_sections(self):
        for group, (path, where) in actions.GROUP_PAGES.items():
            self.assertIn(path.partition("/")[0], window.SECTION_IDS, group)
            self.assertNotIn("Settings", where)


if __name__ == "__main__":
    unittest.main()

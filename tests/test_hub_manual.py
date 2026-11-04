"""The Manual pages render in RedFox Hub: valid markup, working links.

    python3 -m unittest tests.test_hub_manual
"""

import re
import sys
import unittest
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Pango", "1.0")
from gi.repository import Pango  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "files/system/usr/share/redfox/hub"))
from redfox_hub import manual  # noqa: E402

MANUAL = ROOT / "files/system/usr/share/redfox/manual"
HUB_PAGES = {"welcome", "apps", "updates", "settings", "settings/layout", "manual"}


class TestManual(unittest.TestCase):
    def setUp(self):
        manual.MANUAL_DIR = MANUAL
        self.pages = manual.load_pages()

    def test_there_are_pages(self):
        self.assertGreaterEqual(len(self.pages), 5)

    def test_every_page_has_a_title_and_summary(self):
        for page in self.pages:
            self.assertTrue(page.title and page.summary, page.slug)

    def test_every_line_is_valid_markup(self):
        for page in self.pages:
            for line in [page.summary, *page.body.splitlines()]:
                text = re.sub(r"^(##|-|\d+\.)\s+", "", line.strip())
                if not text or text.startswith("```"):
                    continue
                try:
                    # GtkLabel handles <a>; Pango alone doesn't know it.
                    markup = re.sub(r"</?a\b[^>]*>", "", manual.inline(text))
                    Pango.parse_markup(markup, -1, "\0")
                except Exception as error:  # GLib.Error
                    self.fail(f"{page.slug}: {line!r}: {error}")
                self.assertNotIn("](", manual.inline(text), f"{page.slug}: unparsed link in {line!r}")

    def test_links_point_somewhere(self):
        slugs = {page.slug for page in self.pages}
        for page in self.pages:
            for target in re.findall(r"\]\(([^)\s]+)\)", page.body + page.summary):
                if target.startswith("manual:"):
                    self.assertIn(target[7:], slugs, f"{page.slug} links to {target}")
                elif target.startswith("hub:"):
                    self.assertIn(target[4:], HUB_PAGES, f"{page.slug} links to {target}")
                else:
                    self.assertTrue(target.startswith("https://"), f"{page.slug}: {target}")

    def test_no_ujust(self):
        for page in self.pages:
            self.assertNotIn("ujust", page.body + page.summary, page.slug)


if __name__ == "__main__":
    unittest.main()

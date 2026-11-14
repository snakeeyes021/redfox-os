"""Hub's VPN page: how servers and rules are described, and what it hands redfox-nord.

    python3 -m unittest tests.test_hub_vpn
"""

import json
import sys
import unittest
from pathlib import Path

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "files/hub/src"))
    from redfox_hub import vpn
except (ImportError, ValueError):  # no GTK 4 / libadwaita here
    vpn = None


@unittest.skipIf(vpn is None, "RedFox Hub's libraries aren't here")
class VpnText(unittest.TestCase):
    def test_server_title(self):
        self.assertEqual(vpn.server_title({"country_name": "United States", "number": "13024"}),
                         "United States #13024")
        self.assertEqual(vpn.server_title({"country": "UK", "number": "2214"}), "UK #2214")

    def test_server_subtitle(self):
        self.assertEqual(vpn.server_subtitle({"p2p": True, "load": 31, "online": True}), "P2P · Load 31%")
        self.assertEqual(vpn.server_subtitle({"load": 91, "online": True}), "Load 91% · busy")
        self.assertEqual(vpn.server_subtitle({"load": None, "online": False}), "Offline")
        self.assertEqual(vpn.server_subtitle({"load": 12, "online": True, "active": True}),
                         "Load 12% · Connected")
        self.assertEqual(vpn.server_subtitle({"load": None, "online": None}), "")

    def test_rules_payload(self):
        rules = [{"country": "US", "country_name": "United States", "count": 2.0, "p2p": 1}]
        self.assertEqual(json.loads(vpn.rules_payload(rules)), [{"country": "US", "count": 2, "p2p": True}])

    def test_last_line(self):
        self.assertEqual(vpn.last_line("one\n[SUCCESS] Done!\n\n", "x"), "Done!")
        self.assertEqual(vpn.last_line("", "fallback"), "fallback")

    def test_no_dev_hints_in_the_page(self):
        text = Path(vpn.__file__).read_text().lower()
        for hint in ("added later", "for now", "not yet", "coming soon", "not implemented"):
            self.assertNotIn(hint, text)


if __name__ == "__main__":
    unittest.main()

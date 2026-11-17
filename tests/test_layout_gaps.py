"""The layouts' one gap: the floating dock's gap and Tiling Shell's gaps are a single setting
that every layout keeps.

    python3 -m unittest tests.test_layout_gaps
"""

import configparser
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXT = ROOT / "files/system/usr/share/gnome-shell/extensions/redfox-layouts@redfoxlabs.tech/extension.js"
LAYOUT = ROOT / "files/system/usr/bin/redfox-layout"
SCHEMA = ROOT / "files/system/usr/share/glib-2.0/schemas/org.gnome.shell.extensions.redfox-layouts.gschema.xml"
DCONF = ROOT / "files/system/etc/dconf/db/redfox.d/00-redfox"
HUB = ROOT / "files/hub/src/redfox_hub/settings.py"


class OneGap(unittest.TestCase):
    def test_switching_layout_keeps_the_gap(self):
        text = LAYOUT.read_text()
        reset = re.search(r"^RESET_KEYS = \{(.*?)^\}", text, re.S | re.M).group(1)
        self.assertNotIn('"floating-dock-gap"', reset)
        self.assertNotIn("floating-dock-gap", "".join(re.findall(r'"settings": \{.*', text)))

    def test_the_extension_keeps_tiling_gaps_equal_to_it(self):
        text = EXT.read_text()
        self.assertIn("TILING_GAPS = ['inner-gaps', 'outer-gaps']", text)
        self.assertIn("this._syncTilingGaps();", text.split("'changed::floating-dock-gap'")[1].split("},")[0])
        # Tiling Shell's own gap settings change the one gap too.
        self.assertIn("changed::${key}", text)
        self.assertIn("this._tilingGapChanged(key)", text)

    def test_a_tiling_gap_set_before_keeps_its_value(self):
        # A Tiling Shell gap set before (layout-tiling-dewy sets 0) isn't replaced by the dock's
        # default when the one gap was never set: it's adopted first, then synced.
        text = EXT.read_text()
        enable = text[text.index("    enable() {"):text.index("    disable() {")]
        self.assertIn("this._adoptOwnTilingGap();\n        this._syncTilingGaps();", enable)
        adopt = text[text.index("    _adoptOwnTilingGap() {"):text.index("    _syncTilingGaps() {")]
        self.assertIn("get_user_value('floating-dock-gap') !== null", adopt)
        self.assertIn("get_user_value('inner-gaps')", adopt)

    def test_defaults_agree(self):
        root = ET.parse(SCHEMA).getroot()
        gap = next(k for k in root.iter("key") if k.get("name") == "floating-dock-gap")
        dconf = configparser.ConfigParser(interpolation=None)
        dconf.read(DCONF)
        tiling = dconf["org/gnome/shell/extensions/tilingshell"]
        self.assertEqual(gap.findtext("default"), "8")
        self.assertEqual(tiling["inner-gaps"], "uint32 8")
        self.assertEqual(tiling["outer-gaps"], "uint32 8")

    def test_hub_names_it_gaps(self):
        text = HUB.read_text()
        self.assertIn('("floating-dock-gap", 0, 64, 1, "Gaps",', text)
        self.assertNotIn("For the RedFox and Cal layouts", text)


if __name__ == "__main__":
    unittest.main()

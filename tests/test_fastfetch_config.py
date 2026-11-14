"""RedFox's fastfetch config: the OS line shows the RedFox fox (U+10F000 in RedFox Symbols, the
glyph the Starship prompt uses), not the Fedora logo, in the same colour as the other keys.

    python3 -m unittest tests.test_fastfetch_config
"""

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "files/system/usr/share/ublue-os/bazzite/fastfetch.jsonc"
FONT = ROOT / "files/system/usr/share/fonts/redfox-symbols/RedFoxSymbols.ttf"
CATPPUCCIN = ROOT / "files/system/usr/share/redfox/starship/themes/catppuccin-powerline.toml"
FOX = "\U0010f000"


def load_jsonc(path):
    # Drop // comments (outside strings) and trailing commas: enough for this file.
    text = "\n".join(re.sub(r'^((?:[^"/]|"(?:\\.|[^"\\])*")*)//.*$', r"\1", line)
                     for line in path.read_text(encoding="utf-8").splitlines())
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", text))


class FastfetchFox(unittest.TestCase):
    def setUp(self):
        self.config = load_jsonc(CONFIG)
        self.modules = {m["type"]: m for m in self.config["modules"] if isinstance(m, dict)}

    def test_os_line_shows_the_fox(self):
        key = self.modules["os"]["key"]
        self.assertIn(FOX, key)
        self.assertNotIn("\U000f08db", key, "the Fedora logo is gone")

    def test_it_is_the_prompts_fox(self):
        self.assertIn(f'Fedora = "{FOX} "', CATPPUCCIN.read_text(encoding="utf-8"))

    def test_os_key_has_no_colour_of_its_own(self):
        # So it takes the shared key colour, like every other key icon.
        self.assertNotIn("keyColor", self.modules["os"])

    @unittest.skipUnless(shutil.which("fc-query"), "fc-query isn't here")
    def test_the_font_has_the_glyph(self):
        charset = subprocess.run(["fc-query", "--format=%{charset}", str(FONT)],
                                 capture_output=True, text=True, check=True).stdout
        self.assertIn("10f000", charset.split())


if __name__ == "__main__":
    unittest.main()

import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES = ROOT / "files" / "system" / "usr" / "share" / "redfox" / "starship" / "themes"
MAKE = ROOT / "assets" / "starship" / "make-themes.py"
TERMINAL = ROOT / "files" / "system" / "usr" / "bin" / "redfox-terminal"
PROFILE = ROOT / "files" / "system" / "etc" / "profile.d" / "redfox-starship.sh"

loader = importlib.machinery.SourceFileLoader("make_themes", str(MAKE))
spec = importlib.util.spec_from_loader("make_themes", loader)
mt = importlib.util.module_from_spec(spec)
loader.exec_module(mt)


def rows():
    return [line.split("\t") for line in (THEMES / "themes.tsv").read_text().splitlines()
            if not line.startswith("#")]


class TestThemes(unittest.TestCase):
    def test_every_preset_is_a_theme(self):
        ids = [r[0] for r in rows()]
        self.assertEqual(ids[:2], ["redfox", "starship"])
        self.assertEqual(sorted(ids[2:]), sorted(mt.PRESET_NAMES))
        self.assertEqual(len(ids), 14)

    def test_files_exist_and_parse(self):
        for theme_id, name, path, nerd in rows():
            self.assertTrue(name, theme_id)
            self.assertIn(nerd, ("yes", "no"))
            local = ROOT / "files" / "system" / path.lstrip("/")
            self.assertTrue(local.is_file(), path)
            tomllib.loads(local.read_text())

    def test_the_fox_is_the_os_symbol_where_the_os_shows(self):
        if not mt.FOX:
            # No fox yet: the presets are Starship's own, symbols included.
            for theme_id, _name, path, _nerd in rows()[2:]:
                text = (ROOT / "files" / "system" / path.lstrip("/")).read_text()
                upstream = (ROOT / "assets/starship/presets" / f"{theme_id}.toml").read_text()
                self.assertTrue(text.endswith(upstream), theme_id)
            return
        shown = []
        for theme_id, _name, path, _nerd in rows()[2:]:
            data = tomllib.loads((ROOT / "files" / "system" / path.lstrip("/")).read_text())
            os_module = data.get("os", {})
            if os_module.get("disabled") is False:
                shown.append(theme_id)
                for key in mt.FOX_KEYS:
                    self.assertTrue(os_module["symbols"][key].startswith(mt.FOX), (theme_id, key))
        self.assertEqual(sorted(shown), ["catppuccin-powerline", "gruvbox-rainbow", "tokyo-night"])

    def test_generated_files_are_up_to_date(self):
        with tempfile.TemporaryDirectory() as d:
            copy = Path(d) / "repo"
            for sub in ("assets/starship",):
                shutil.copytree(ROOT / sub, copy / sub)
            subprocess.run(["python3", "-I", str(copy / "assets/starship/make-themes.py")],
                           check=True, capture_output=True)
            out = copy / "files/system/usr/share/redfox/starship/themes"
            for f in out.iterdir():
                self.assertEqual(f.read_text(), (THEMES / f.name).read_text(), f.name)
            self.assertEqual(sorted(p.name for p in out.iterdir()),
                             sorted(p.name for p in THEMES.iterdir()))

    def test_licence_ships_with_the_presets(self):
        self.assertIn("ISC License", (THEMES / "LICENSE").read_text())


class TestRedfoxTerminal(unittest.TestCase):
    def run_terminal(self, home, *args):
        env = {"HOME": str(home), "PATH": os.environ["PATH"],
               "REDFOX_STARSHIP_THEMES": str(THEMES / "themes.tsv")}
        return subprocess.run(["bash", str(TERMINAL), *args], env=env, capture_output=True,
                              text=True)

    def test_choosing_a_theme(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            # The prompt is already on, so choosing a theme needs no Homebrew.
            (home / ".bashrc").write_text("# >>> redfox-terminal prompt >>>\n"
                                          "eval\n# <<< redfox-terminal prompt <<<\n")
            data = json.loads(self.run_terminal(home, "prompt", "themes", "--json").stdout)
            self.assertEqual((data["on"], data["current"], data["own_config"]), (True, "redfox", False))
            self.assertEqual(len(data["themes"]), 14)
            r = self.run_terminal(home, "prompt", "theme", "tokyo-night")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual((home / ".config/redfox/starship-theme").read_text().strip(), "tokyo-night")
            status = json.loads(self.run_terminal(home, "status", "--json").stdout)
            self.assertEqual(status["theme"], "tokyo-night")
            self.assertEqual(self.run_terminal(home, "prompt", "theme", "nope").returncode, 2)

    def test_the_shell_picks_the_theme_file(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            (home / ".config/redfox").mkdir(parents=True)
            (home / ".config/redfox/starship-theme").write_text("gruvbox-rainbow\n")
            script = PROFILE.read_text().replace("/usr/share/redfox/starship/themes/themes.tsv",
                                                 str(THEMES / "themes.tsv"))
            (home / "p.sh").write_text(script)
            out = subprocess.run(["sh", "-c", f'. "{home}/p.sh"; echo "$STARSHIP_CONFIG"; '
                                  f'echo redfox > "{home}/.config/redfox/starship-theme"; '
                                  f'. "{home}/p.sh"; echo "$STARSHIP_CONFIG"'],
                                 env={"HOME": str(home), "PATH": os.environ["PATH"]},
                                 capture_output=True, text=True).stdout.split()
            self.assertEqual(out, ["/usr/share/redfox/starship/themes/gruvbox-rainbow.toml",
                                   "/usr/share/redfox/starship.toml"])


if __name__ == "__main__":
    unittest.main()

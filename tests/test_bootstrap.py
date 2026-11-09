"""The bootstrap and RedFox Hub change things the same way.

- redfox-bootstrap lists each profile's stages and steps from the recipes,
  and runs `ujust bootstrap-<id>`.
- Every bootstrap step with a Hub switch uses the same tool as the switch
  (apps at login, the layout, Midikeep), so Hub shows the result.
- redfox-autostart handles Steam (no autostart on new accounts; a switch).
- New accounts start in the RedFox layout, once.
"""

import importlib.machinery
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYSTEM = ROOT / "files" / "system"
BOOTSTRAP = SYSTEM / "usr" / "bin" / "redfox-bootstrap"
AUTOSTART = SYSTEM / "usr" / "bin" / "redfox-autostart"
TOGGLES = SYSTEM / "usr" / "bin" / "redfox-toggles"
JUSTFILE = SYSTEM / "usr" / "share" / "ublue-os" / "just" / "60-custom.just"
HOOK = SYSTEM / "usr" / "share" / "redfox" / "user-setup.hooks.d" / "30-new-account-layout.sh"
SKEL_MARKER = SYSTEM / "etc" / "skel" / ".config" / "redfox" / "new-account"
NO_STEAM = ROOT / "files" / "scripts" / "no-steam-autostart.sh"
RECIPE = ROOT / "recipes" / "_common-modules.yml"
OVERRIDE = ROOT / "files" / "gschema-overrides" / "zz99-redfox.gschema.override"


def load(path, name):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def recipe_bodies():
    """Recipe name -> (dependencies, body text), from 60-custom.just."""
    out, name = {}, None
    for line in JUSTFILE.read_text().splitlines():
        match = re.match(r"^([a-z0-9_-]+)(?: [^:]*)?:(?!=)(.*)$", line)
        if match:
            name = match.group(1)
            out[name] = (match.group(2).split(), [])
        elif name and line.startswith((" ", "\t")):
            out[name][1].append(line.strip())
        elif line.strip() and not line.startswith("#"):
            name = None
    return {k: (deps, "\n".join(body)) for k, (deps, body) in out.items()}


class TestBootstrapList(unittest.TestCase):
    @unittest.skipUnless(shutil.which("just"), "just isn't installed")
    def test_profiles_from_recipes(self):
        rb = load(BOOTSTRAP, "redfox_bootstrap")
        with tempfile.TemporaryDirectory() as tmp:
            just = Path(tmp, "justfile")
            just.write_text(
                "_reset:\n    true\n\n"
                "# Configure it\nconfigure-matt: step-a step-b\n\n"
                "# Step A\nstep-a:\n    true\n\n"
                "step-b:\n    true\n\n"
                "# Install it\ninstall-matt:\n    true\n\n"
                "bootstrap-matt: _reset configure-matt install-matt\n")
            rb.JUSTFILE = str(just)
            data = rb.list_profiles()
        profiles = {p["id"]: p for p in data["profiles"]}
        self.assertEqual(list(profiles), ["matt"])   # profiles without a recipe are left out
        stages = profiles["matt"]["stages"]
        self.assertEqual([s["doc"] for s in stages], ["Configure it", "Install it"])
        self.assertEqual(stages[0]["steps"], [{"recipe": "step-a", "doc": "Step A"},
                                              {"recipe": "step-b", "doc": "step-b"}])
        self.assertEqual(stages[1]["steps"], [])

    def test_every_profile_has_a_bootstrap_recipe(self):
        rb = load(BOOTSTRAP, "redfox_bootstrap")
        bodies = recipe_bodies()
        for profile in rb.PROFILES:
            self.assertIn(f"bootstrap-{profile['id']}", bodies)
            self.assertNotRegex(profile["summary"], r"\b(his|her|he|she)\b")


class TestSameToolsAsHub(unittest.TestCase):
    def test_tray_apps_through_redfox_autostart(self):
        bodies = recipe_bodies()
        self.assertIn("configure-autostart-tray", bodies["configure-matt"][0])
        self.assertIn("/usr/bin/redfox-autostart on", bodies["configure-autostart-tray"][1])

    def test_layout_presets_through_redfox_layout(self):
        bodies = recipe_bodies()
        for name, (_deps, body) in bodies.items():
            if name.startswith("preset-dock-"):
                # (preset-dock-redfox also sets the gap, the same key Hub's Layout page edits)
                self.assertRegex(body.splitlines()[0], r"^redfox-layout set \w+$", name)

    def test_midikeep_through_hubs_command(self):
        toggles = load(TOGGLES, "redfox_toggles_b")
        midikeep = toggles.BY_ID["midikeep"]
        self.assertEqual(midikeep["on"], ["ujust", "enable-midikeep"])
        self.assertIn("enable-midikeep", recipe_bodies()["configure-music"][0])


class TestSteam(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        (base / "bin").mkdir()
        steam = base / "bin" / "bazzite-steam"
        steam.write_text("#!/bin/sh\n")
        steam.chmod(0o755)
        flatpak = base / "bin" / "flatpak"
        flatpak.write_text("#!/bin/sh\nexit 1\n")
        flatpak.chmod(0o755)
        self.env = dict(os.environ, HOME=str(base / "home"), XDG_CONFIG_HOME=str(base / "home/.config"),
                        XDG_DATA_HOME=str(base / "home/.local/share"),
                        PATH=f"{base / 'bin'}:{os.environ['PATH']}")
        self.entry = base / "home/.config/autostart/steam.desktop"

    def autostart(self, *args):
        return subprocess.run(["bash", str(AUTOSTART), *args], env=self.env, capture_output=True,
                              text=True)

    def steam(self):
        apps = json.loads(self.autostart("list", "--json").stdout)["apps"]
        return next(a for a in apps if a["id"] == "steam")

    def test_on_and_off(self):
        self.assertEqual(self.steam(), {"id": "steam", "name": "Steam", "installed": True, "on": False})
        self.assertEqual(self.autostart("on", "steam").returncode, 0)
        self.assertIn("-silent", self.entry.read_text())
        self.assertTrue(self.steam()["on"])
        self.assertEqual(self.autostart("off", "steam").returncode, 0)
        self.assertFalse(self.entry.exists())

    def test_bazzites_own_entry_counts_and_can_be_turned_off(self):
        self.entry.parent.mkdir(parents=True)
        self.entry.write_text("[Desktop Entry]\nExec=/usr/bin/bazzite-steam -silent %U\n")
        self.assertTrue(self.steam()["on"])
        self.autostart("off", "steam")
        self.assertFalse(self.entry.exists())

    def test_new_accounts_dont_get_it(self):
        self.assertIn("rm -f /etc/skel/.config/autostart/steam.desktop", NO_STEAM.read_text())
        self.assertIn("- no-steam-autostart.sh", RECIPE.read_text())


class TestNewAccounts(unittest.TestCase):
    def run_hook(self, marker):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "bin").mkdir()
            log = base / "calls"
            fake = base / "bin" / "redfox-layout"
            fake.write_text(f'#!/bin/sh\necho "$@" >> {log}\n')
            fake.chmod(0o755)
            config = base / "home/.config"
            if marker:
                (config / "redfox").mkdir(parents=True)
                (config / "redfox/new-account").write_text("")
            env = dict(os.environ, HOME=str(base / "home"), XDG_CONFIG_HOME=str(config),
                       PATH=f"{base / 'bin'}:{os.environ['PATH']}")
            for _ in range(2):
                subprocess.run(["bash", str(HOOK)], env=env, check=True)
            return (log.read_text() if log.exists() else ""), (config / "redfox/new-account").exists()

    def test_new_account_once(self):
        calls, left = self.run_hook(marker=True)
        self.assertEqual(calls, "set redfox\n")
        self.assertFalse(left)

    def test_existing_account_untouched(self):
        calls, _ = self.run_hook(marker=False)
        self.assertEqual(calls, "")

    def test_marker_ships_in_skel(self):
        self.assertTrue(SKEL_MARKER.is_file())


class TestDock(unittest.TestCase):
    def test_hub_last(self):
        line = next(l for l in OVERRIDE.read_text().splitlines() if l.startswith("favorite-apps="))
        apps = re.findall(r"'([^']+)'", line)
        self.assertEqual(apps, ["org.gnome.Nautilus.desktop", "org.mozilla.firefox.desktop",
                                "org.gnome.Calculator.desktop", "org.gnome.TextEditor.desktop",
                                "io.github.kolunmi.Bazaar.desktop", "org.gnome.Settings.desktop",
                                "tech.redfoxlabs.Hub.desktop"])


if __name__ == "__main__":
    unittest.main()

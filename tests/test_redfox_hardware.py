import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SYSTEM = ROOT / "files" / "system"
HARDWARE = SYSTEM / "usr" / "bin" / "redfox-hardware"
HARDWARE_ROOT = SYSTEM / "usr" / "libexec" / "redfox-hardware-root"
ACTION_HELPER = SYSTEM / "usr" / "libexec" / "redfox-system-action"
CATALOG = SYSTEM / "usr" / "share" / "redfox" / "software.yaml"
CHECKER = ROOT / "tests" / "check_bazzite_recipes.py"
RECORD = ROOT / "tests" / "bazzite-recipes.json"
IDS = ["asus", "coolercontrol", "displaylink", "openrazer", "opentabletdriver", "boxtron"]


def run(argv, env=None):
    return subprocess.run(["bash", *map(str, argv)], capture_output=True, text=True,
                          env=env or dict(os.environ))


class TestHardware(unittest.TestCase):
    def test_refuses_anything_else(self):
        for args in ([], ["asus"], ["nope", "install"], ["asus", "maybe"],
                     ["asus", "install", "extra"]):
            self.assertEqual(run([HARDWARE, *args]).returncode, 2, args)

    def test_root_helper_refuses_anything_else(self):
        for args in ([], ["boxtron", "install"], ["asus", "status"], ["../x", "install"]):
            self.assertEqual(run([HARDWARE_ROOT, *args]).returncode, 2, args)

    def test_root_steps_go_through_pkexec_and_the_action_helper(self):
        with tempfile.TemporaryDirectory() as tmp:
            bindir = Path(tmp, "bin")
            bindir.mkdir()
            log = Path(tmp, "calls")
            fake = bindir / "pkexec"
            fake.write_text(f'#!/bin/sh\necho "$@" >> {log}\n')
            fake.chmod(0o755)
            env = dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}", HOME=tmp)
            for hw in ("asus", "coolercontrol", "displaylink"):
                for verb in ("install", "remove"):
                    self.assertEqual(run([HARDWARE, hw, verb], env).returncode, 0, (hw, verb))
            calls = log.read_text().splitlines()
        self.assertEqual(calls[0], "/usr/libexec/redfox-system-action hardware asus install")
        self.assertEqual(len(calls), 6)

    def test_action_helper_passes_hardware_on(self):
        text = ACTION_HELPER.read_text()
        self.assertIn('exec /usr/libexec/redfox-hardware-root "$2" "$3"', text)
        self.assertEqual(run([ACTION_HELPER, "hardware", "asus"]).returncode, 2)

    def test_status(self):
        with tempfile.TemporaryDirectory() as home:
            env = dict(os.environ, HOME=home)
            self.assertEqual(run([HARDWARE, "boxtron", "status"], env).stdout.strip(),
                             "not-installed")
            Path(home, ".local/share/Steam/compatibilitytools.d/boxtron").mkdir(parents=True)
            self.assertEqual(run([HARDWARE, "boxtron", "status"], env).stdout.strip(), "installed")
            self.assertEqual(run([HARDWARE, "openrazer", "status"], env).stdout.strip(),
                             "not-installed")

    def test_the_asus_download_is_pinned_and_checked(self):
        text = HARDWARE_ROOT.read_text()
        self.assertRegex(text, r"ASUS_SHA256=[0-9a-f]{64}\n")
        self.assertIn("sha256sum --check", text)

    def test_catalog_items(self):
        items = {i["id"]: i for i in yaml.safe_load(CATALOG.read_text())["items"]}
        for hw in IDS:
            self.assertEqual(items[hw]["install"], f"redfox-hardware {hw} install")
            self.assertEqual(items[hw]["remove"], f"redfox-hardware {hw} remove")
        for hw in ("displaylink", "openrazer", "opentabletdriver"):
            self.assertTrue(items[hw].get("restart"), hw)


class TestBazziteRecipes(unittest.TestCase):
    def test_every_recorded_recipe_names_our_version(self):
        record = json.loads(RECORD.read_text())["recipes"]
        for name in ("asus", "install-coolercontrol", "install-displaylink", "install-openrazer",
                     "opentabletdriver", "install-boxtron"):
            self.assertIn(name, record)
        for name, entry in record.items():
            self.assertTrue((ROOT / entry["ours"]).is_file(), name)
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$", name)

    def test_flags_a_changed_recipe(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("check", CHECKER)
        check = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(check)
        with tempfile.TemporaryDirectory() as just:
            Path(just, "80-x.just").write_text(
                'asus ACTION="":\n    echo one\n\n    echo two\n\nalias a := asus\nother:\n    true\n')
            found = check.recipes(just)
            self.assertEqual(found["asus"], 'asus ACTION="":\n    echo one\n\n    echo two')
            self.assertNotIn("alias", found)
            record = {"recipes": {"asus": {"ours": "x", "sha256": check.digest(found["asus"])}}}
            original = check.RECORD
            try:
                check.RECORD = Path(just, "record.json")
                check.RECORD.write_text(json.dumps(record))
                self.assertEqual(check.main(["x", just]), 0)
                Path(just, "80-x.just").write_text('asus ACTION="":\n    echo changed\n')
                self.assertEqual(check.main(["x", just]), 1)
            finally:
                check.RECORD = original


if __name__ == "__main__":
    unittest.main()

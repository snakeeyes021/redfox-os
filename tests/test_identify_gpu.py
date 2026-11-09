"""extras/identify_gpu.sh and .ps1 name the right download for every case in
tests/gpu-cases.json, using the rules file in the repo (no network). The
PowerShell half runs where `pwsh` is installed."""

import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SH = ROOT / "extras" / "identify_gpu.sh"
PS1 = ROOT / "extras" / "identify_gpu.ps1"
RULES = ROOT / "files" / "system" / "usr" / "share" / "redfox" / "gpu-rules.json"
CASES = json.loads((ROOT / "tests" / "gpu-cases.json").read_text())
TITLES = {
    "redfox-os": "RedFoxOS (Intel & AMD)",
    "redfox-os-nvidia": "RedFoxOS NVIDIA",
    "redfox-os-nvidia-legacy": "RedFoxOS NVIDIA Legacy",
}


def run(argv, devices, rules=RULES):
    env = dict(os.environ, RFX_DEVICES=" ".join(f"{v}:{d}" for v, d in devices),
               RFX_RULES_FILE=str(rules))
    res = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=120)
    return res.returncode, res.stdout


class Checks:
    argv = None

    def check_case(self, case):
        rc, out = run(self.argv, case["devices"])
        self.assertEqual(rc, 0, out)
        code = "RFX1 " + (" ".join(f"{v}:{d}" for v, d in case["devices"]) or "none")
        if case["image"]:
            self.assertIn(f"Works best on your machine: {TITLES[case['image']]}\n", out, case["name"])
            self.assertIn("the page opens with it picked", out)
        else:
            self.assertIn("No single download works best on your machine", out, case["name"])
        self.assertEqual("Two graphics chips" in out, bool(case.get("hybrid")), case["name"])
        self.assertIn("https://redfoxlabs.tech/download/#gpu=" + code.replace(" ", "+"), out)
        self.assertIn(code, out)

    def test_every_case(self):
        for case in CASES:
            with self.subTest(case["name"]):
                self.check_case(case)

    def test_without_rules_it_prints_the_code(self):
        rc, out = run(self.argv, [["8086", "46a6"]], rules="/nonexistent/rules.json")
        self.assertEqual(rc, 0, out)
        self.assertIn("Couldn't decide here", out)
        self.assertIn("    RFX1 8086:46a6\n", out)
        self.assertIn("https://redfoxlabs.tech/download/#gpu=RFX1+8086:46a6", out)
        self.assertNotIn("Works best on your machine:", out)


class TestShell(Checks, unittest.TestCase):
    argv = ["bash", str(SH)]


@unittest.skipUnless(shutil.which("pwsh"), "PowerShell (pwsh) isn't installed")
class TestPowerShell(Checks, unittest.TestCase):
    argv = ["pwsh", "-NoProfile", "-NonInteractive", "-File", str(PS1)]


if __name__ == "__main__":
    unittest.main()

"""extras/identify_gpu.sh and .ps1 name the right download for every case in
tests/gpu-cases.json, using the rules file in the repo (no network), and
print exactly the same thing.

The PowerShell half runs where `pwsh` is installed, or with RFX_PWSH set to
a command that runs it, e.g. a container:
  RFX_PWSH="podman run --rm -i -v $PWD:$PWD:ro,z -w $PWD \
    -e RFX_DEVICES -e RFX_RULES_FILE mcr.microsoft.com/powershell pwsh"
"""

import json
import os
import shlex
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SH = ROOT / "extras" / "identify_gpu.sh"
PS1 = ROOT / "extras" / "identify_gpu.ps1"
RULES = ROOT / "files" / "system" / "usr" / "share" / "redfox" / "gpu-rules.json"
CASES = json.loads((ROOT / "tests" / "gpu-cases.json").read_text())
PAGE = "https://redfoxlabs.tech/download/"
# Each download's name, as on the download page and in RedFox Hub
DOWNLOADS = {
    "redfox-os": "RedFoxOS (AMD & Intel)",
    "redfox-os-nvidia": "RedFoxOS NVIDIA (GTX 16xx, RTX 20xx and newer)",
    "redfox-os-nvidia-legacy": "RedFoxOS NVIDIA Legacy (GTX 10xx, 9xx and 750)",
}
PWSH = shlex.split(os.environ.get("RFX_PWSH", "pwsh"))
HAVE_PWSH = "RFX_PWSH" in os.environ or shutil.which("pwsh") is not None


def run(argv, devices, rules=RULES):
    env = dict(os.environ, RFX_DEVICES=" ".join(f"{v}:{d}" for v, d in devices),
               RFX_RULES_FILE=str(rules))
    res = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=180)
    return res.returncode, res.stdout.replace("\r\n", "\n")


class Checks:
    argv = None

    def check_case(self, case):
        rc, out = run(self.argv, case["devices"])
        self.assertEqual(rc, 0, out)
        lines = out.splitlines()
        self.assertEqual(lines[0], "RedFoxOS graphics check")
        for v, d in case["devices"]:
            self.assertIn(f"  {v}:{d}", lines)
        if case["image"]:
            self.assertIn(f"The download to get:\n  {DOWNLOADS[case['image']]}\n", out, case["name"])
            self.assertIn(f"Get it at:\n  {PAGE}\n", out)
        else:
            self.assertIn("No single download works best on your machine:", out, case["name"])
            self.assertIn(f"The downloads are at:\n  {PAGE}\n", out)
        self.assertEqual("Two graphics chips:" in out, bool(case.get("hybrid")), case["name"])
        self.assertTrue(out.endswith("Nothing about this computer has been sent anywhere.\n"))
        # No paste code, no pre-selected link, and lines a terminal shows whole
        self.assertNotIn("RFX1", out)
        self.assertNotIn("#gpu", out)
        self.assertTrue(all(len(line) <= 80 for line in lines), out)

    def test_every_case(self):
        for case in CASES:
            with self.subTest(case["name"]):
                self.check_case(case)

    def test_without_rules(self):
        rc, out = run(self.argv, [["8086", "46a6"]], rules="/nonexistent/rules.json")
        self.assertEqual(rc, 0, out)
        self.assertIn("Couldn't download RedFoxOS's graphics rules", out)
        self.assertIn(f"  {PAGE}\n", out)
        self.assertNotIn("The download to get:", out)


class TestShell(Checks, unittest.TestCase):
    argv = ["bash", str(SH)]


@unittest.skipUnless(HAVE_PWSH, "PowerShell (pwsh) isn't installed")
class TestPowerShell(Checks, unittest.TestCase):
    argv = PWSH + ["-NoProfile", "-NonInteractive", "-File", str(PS1)]


@unittest.skipUnless(HAVE_PWSH, "PowerShell (pwsh) isn't installed")
class TestSameOutput(unittest.TestCase):
    def test_both_print_the_same(self):
        cases = [c["devices"] for c in CASES] + [[]]
        for devices in cases:
            with self.subTest(devices):
                self.assertEqual(run(TestShell.argv, devices), run(TestPowerShell.argv, devices))
        offline = [["8086", "46a6"]]
        self.assertEqual(run(TestShell.argv, offline, rules="/nonexistent/rules.json"),
                         run(TestPowerShell.argv, offline, rules="/nonexistent/rules.json"))


if __name__ == "__main__":
    unittest.main()

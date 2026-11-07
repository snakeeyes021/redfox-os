"""redfox-rollback-helper's image recommendation, from faked PCI devices.

    python3 -m unittest tests.test_rollback_helper

Needs rpm-ostree (the helper reads the booted image); skipped without it.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HELPER = Path(__file__).resolve().parent.parent / "files/system/usr/bin/redfox-rollback-helper"

REPO = Path(__file__).resolve().parent.parent
RULES = REPO / "files/system/usr/share/redfox/gpu-rules.json"
# Shared with the download page on redfoxlabs.tech, which runs the same cases.
CASES = json.loads((REPO / "tests/gpu-cases.json").read_text())


@unittest.skipUnless(shutil.which("rpm-ostree"), "needs rpm-ostree")
class TestRecommend(unittest.TestCase):
    def run_case(self, devices):
        with tempfile.TemporaryDirectory() as root:
            for n, (vendor, device) in enumerate(devices):
                d = Path(root) / f"0000:0{n}:00.0"
                d.mkdir()
                (d / "vendor").write_text(f"0x{vendor}\n")
                (d / "device").write_text(f"0x{device}\n")
                (d / "class").write_text("0x030000\n")
            out = subprocess.run([str(HELPER), "--json", "images"], capture_output=True, text=True,
                                 env={**os.environ, "REDFOX_PCI_ROOT": root,
                                      "REDFOX_GPU_RULES": str(RULES)}, check=True).stdout
        return json.loads(out)

    def test_non_display_devices_are_ignored(self):
        with tempfile.TemporaryDirectory() as root:
            d = Path(root) / "0000:00:02.0"
            d.mkdir()
            (d / "vendor").write_text("0x10de\n")
            (d / "device").write_text("0x1c03\n")
            (d / "class").write_text("0x060000\n")  # a bridge, not a display
            out = subprocess.run([str(HELPER), "--json", "images"], capture_output=True, text=True,
                                 env={**os.environ, "REDFOX_PCI_ROOT": root,
                                      "REDFOX_GPU_RULES": str(RULES)}, check=True).stdout
        self.assertIsNone(json.loads(out)["recommended"])

    def test_cases(self):
        for case in CASES:
            with self.subTest(case["name"]):
                data = self.run_case(case["devices"])
                self.assertEqual(data["recommended"], case["image"], data["detected"])
                self.assertTrue(data["detected"])


if __name__ == "__main__":
    unittest.main()

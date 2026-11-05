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

CASES = [
    # name, [(vendor, device, class)], recommended
    ("Intel only", [("8086", "46a6", "030000")], "redfox-os"),
    ("AMD only", [("1002", "73bf", "030000")], "redfox-os"),
    ("hybrid Intel + RTX 4060", [("8086", "a7a0", "030000"), ("10de", "28e0", "030200")], "redfox-os-nvidia"),
    ("GTX 1650 (Turing)", [("10de", "1f82", "030000")], "redfox-os-nvidia"),
    ("GTX 1060", [("10de", "1c03", "030000")], "redfox-os-nvidia-legacy"),
    ("hybrid AMD + GTX 1050", [("1002", "1636", "030000"), ("10de", "1c8d", "030200")], "redfox-os-nvidia-legacy"),
    ("NVIDIA of both kinds", [("10de", "2484", "030000"), ("10de", "1b80", "030000")], None),
    ("virtual machine", [("1af4", "1050", "030000")], None),
    ("Intel plus something unknown", [("8086", "46a6", "030000"), ("1234", "1111", "030000")], None),
    ("no display device", [("8086", "1234", "060000")], None),
]


@unittest.skipUnless(shutil.which("rpm-ostree"), "needs rpm-ostree")
class TestRecommend(unittest.TestCase):
    def run_case(self, devices):
        with tempfile.TemporaryDirectory() as root:
            for n, (vendor, device, cls) in enumerate(devices):
                d = Path(root) / f"0000:0{n}:00.0"
                d.mkdir()
                (d / "vendor").write_text(f"0x{vendor}\n")
                (d / "device").write_text(f"0x{device}\n")
                (d / "class").write_text(f"0x{cls}\n")
            out = subprocess.run([str(HELPER), "--json", "images"], capture_output=True, text=True,
                                 env={**os.environ, "REDFOX_PCI_ROOT": root}, check=True).stdout
        return json.loads(out)

    def test_cases(self):
        for name, devices, expected in CASES:
            with self.subTest(name):
                data = self.run_case(devices)
                self.assertEqual(data["recommended"], expected, data["detected"])
                self.assertTrue(data["detected"])


if __name__ == "__main__":
    unittest.main()

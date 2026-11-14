"""bluefin-dx-groups gives every administrator docker, incus-admin and libvirt, and takes
them away again when an account stops being an administrator. Runs the script (not as
root) against a scratch /etc with fake getent, id, usermod, gpasswd and systemd tools.

    python3 -m unittest tests.test_dx_groups
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "files" / "system" / "usr" / "bin" / "bluefin-dx-groups"

# A tiny group database in $REDFOX_TEST_ROOT/etc/group ("name:x:gid:a,b").
FAKES = {
    "getent": """#!/bin/bash
grep "^$2:" "$REDFOX_TEST_ROOT/etc/group" || exit 2
""",
    "id": """#!/bin/bash
if [ "$1" = -u ]; then echo 1000; exit 0; fi
user=${@: -1}
grep -q "^$user:" "$REDFOX_TEST_ROOT/etc/passwd" || exit 1
if [ "$1" = -nG ]; then
  awk -F: -v u="$user" '{ n = split($4, m, ","); for (i = 1; i <= n; i++) if (m[i] == u) printf "%s ", $1 }' \\
      "$REDFOX_TEST_ROOT/etc/group"; echo
fi
""",
    "usermod": """#!/bin/bash
group=$2 user=$3
[ -f "$REDFOX_TEST_ROOT/fail-$user" ] && exit 1
awk -F: -v OFS=: -v g="$group" -v u="$user" '$1 == g { $4 = ($4 == "" ? u : $4 "," u) } 1' \\
    "$REDFOX_TEST_ROOT/etc/group" > "$REDFOX_TEST_ROOT/g.tmp" && mv "$REDFOX_TEST_ROOT/g.tmp" "$REDFOX_TEST_ROOT/etc/group"
echo "usermod $group $user" >> "$REDFOX_TEST_ROOT/calls"
""",
    "gpasswd": """#!/bin/bash
user=$2 group=$3
awk -F: -v OFS=: -v g="$group" -v u="$user" '$1 == g { n = split($4, m, ","); s = ""; for (i = 1; i <= n; i++) if (m[i] != u) s = (s == "" ? m[i] : s "," m[i]); $4 = s } 1' \\
    "$REDFOX_TEST_ROOT/etc/group" > "$REDFOX_TEST_ROOT/g.tmp" && mv "$REDFOX_TEST_ROOT/g.tmp" "$REDFOX_TEST_ROOT/etc/group"
echo "gpasswd $group $user" >> "$REDFOX_TEST_ROOT/calls"
""",
    "systemd-sysusers": "#!/bin/bash\nexit 0\n",
    "systemd-tmpfiles": "#!/bin/bash\nexit 0\n",
}


class DxGroups(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        (self.root / "etc").mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        for name, body in FAKES.items():
            (self.bin / name).write_text(body)
            (self.bin / name).chmod(0o755)
        (self.root / "etc" / "passwd").write_text("ann:x\nben:x\ncat:x\n")
        self.groups({"wheel": "ann,ben", "docker": "cat", "incus-admin": "", "libvirt": ""})

    def groups(self, members):
        (self.root / "etc" / "group").write_text(
            "".join(f"{g}:x:{900 + i}:{m}\n" for i, (g, m) in enumerate(members.items())))

    def members(self):
        rows = (line.split(":") for line in (self.root / "etc" / "group").read_text().splitlines())
        return {r[0]: sorted(filter(None, r[3].split(","))) for r in rows}

    def run_script(self):
        env = dict(os.environ, REDFOX_TEST_ROOT=str(self.root), PATH=f"{self.bin}:{os.environ['PATH']}")
        res = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        return res.stdout

    def test_every_administrator_gets_the_groups(self):
        self.run_script()
        m = self.members()
        self.assertEqual(m["docker"], ["ann", "ben", "cat"])
        self.assertEqual(m["incus-admin"], ["ann", "ben"])
        self.assertEqual(m["libvirt"], ["ann", "ben"])
        self.assertEqual((self.root / "etc/ublue/dx-groups").read_text().strip(), "5")

    def test_a_demoted_administrator_loses_them_at_the_next_start(self):
        self.run_script()
        m = {g: ",".join(v) for g, v in self.members().items()}
        self.groups(dict(m, wheel="ann"))  # ben is no longer an administrator
        out = self.run_script()
        m = self.members()
        self.assertNotIn("ben", m["docker"] + m["incus-admin"] + m["libvirt"])
        self.assertEqual(m["docker"], ["ann", "cat"], "a standard account added by hand keeps docker")
        self.assertIn("Took ben out of docker", out)
        self.assertNotIn("ben:", (self.root / "etc/ublue/dx-groups-managed").read_text())

    def test_one_account_that_cannot_be_changed_does_not_stop_the_others(self):
        (self.root / "fail-ann").touch()
        out = self.run_script()
        m = self.members()
        self.assertEqual(m["libvirt"], ["ben"])
        self.assertIn("Couldn't add ann to libvirt", out)

    def test_overrides_are_ignored_as_root(self):
        text = SCRIPT.read_text()
        self.assertIn('[ "$(id -u)" -ne 0 ] && ROOT="${REDFOX_TEST_ROOT:-}"', text)


if __name__ == "__main__":
    unittest.main()

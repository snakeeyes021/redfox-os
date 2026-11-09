import importlib.machinery
import importlib.util
import os
import tempfile
import unittest
import unittest.mock
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = ROOT / "files" / "system" / "usr" / "bin" / "redfox-logs"

loader = importlib.machinery.SourceFileLoader("redfox_logs", str(CLI_PATH))
spec = importlib.util.spec_from_loader("redfox_logs", loader)
rl = importlib.util.module_from_spec(spec)
loader.exec_module(rl)

# A made-up computer: user "kestrel", host "otterbox", Wi-Fi "Harbour Lights".
NMCLI_CONNECTIONS = b"Harbour Lights:802-11-wireless\nWired connection 1:802-3-ethernet\nlo:loopback\n"


def fake_run(argv, timeout=60):
    joined = " ".join(argv)
    if joined.startswith("nmcli -t -f NAME,TYPE"):
        return NMCLI_CONNECTIONS
    if joined.startswith("nmcli -t -f SSID"):
        return b"Harbour Lights\nCorner Cafe Guest\n"
    if joined.startswith("lsblk -dno SERIAL"):
        return b"S6XNNF0R123456\n\n"
    return b""


class FakePw:
    pw_name = "kestrel"
    pw_gecos = "Robin Kestrelson,,,"


class TestRedaction(unittest.TestCase):
    def setUp(self):
        patches = [
            unittest.mock.patch.object(rl, "run", fake_run),
            unittest.mock.patch.object(rl.pwd, "getpwuid", lambda _uid: FakePw),
            unittest.mock.patch.object(rl.socket, "gethostname", lambda: "otterbox.local"),
            unittest.mock.patch.object(rl, "read", lambda path: {
                "/etc/machine-id": b"0123456789abcdef0123456789abcdef",
                "/etc/hostname": b"otterbox"}.get(path, b"")),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        with unittest.mock.patch.dict(os.environ, {"HOME": "/home/kestrel"}):
            self.personal = rl.personal_patterns()

    def clean(self, text):
        return rl.redact(text.encode(), self.personal).decode()

    def test_personal_details(self):
        log = ("Nov 08 otterbox systemd[1234]: Started app in /home/kestrel/Projects.\n"
               "user kestrel logged in; Robin Kestrelson; Robin's notes\n"
               "wlp3s0: connected to Harbour Lights (aa:bb:cc:dd:ee:ff); saw Corner Cafe Guest\n"
               "machine 0123456789abcdef0123456789abcdef disk S6XNNF0R123456\n"
               "mail robin@example.org token=abc123def456ghi789 Bearer abc.def-ghi\n"
               "Serial Number: XK12-9981 serial console ready\n")
        out = self.clean(log)
        for secret in ("otterbox", "kestrel", "Kestrelson", "Harbour Lights", "Corner Cafe",
                       "aa:bb:cc", "0123456789abcdef", "S6XNNF0R123456", "robin@example.org",
                       "abc123def456", "abc.def-ghi", "XK12-9981"):
            self.assertNotIn(secret, out, secret)
        self.assertIn("/home/<user>/Projects", out)
        self.assertIn("<computer> systemd[1234]", out)
        self.assertIn("serial console ready", out)   # a word, not a serial
        self.assertIn("Wired connection 1", rl.redact(b"Wired connection 1 up", self.personal).decode())

    def test_names_inside_longer_words_stay(self):
        self.assertEqual(self.clean("kestrels and otterboxes"), "kestrels and otterboxes")

    def test_zip(self):
        with tempfile.TemporaryDirectory() as out, \
                unittest.mock.patch.object(rl, "system_info", lambda: b"host otterbox\n"), \
                unittest.mock.patch.object(rl, "FILES", [("journal-this-boot.txt", ["x"])]), \
                unittest.mock.patch.object(rl, "run", lambda argv, timeout=60:
                                           b"kestrel@otterbox: hello\n"
                                           if argv == ["x"] else fake_run(argv)), \
                unittest.mock.patch.dict(os.environ, {"HOME": "/home/kestrel"}), \
                unittest.mock.patch("builtins.print"):
            path = rl.write_zip(out)
            self.assertEqual(oct(os.stat(path).st_mode & 0o777), "0o600")
            with zipfile.ZipFile(path) as z:
                self.assertEqual(sorted(z.namelist()),
                                 ["README.txt", "journal-this-boot.txt", "system-info.txt"])
                self.assertEqual(z.read("journal-this-boot.txt"), b"<user>@<computer>: hello\n")
                self.assertEqual(z.read("system-info.txt"), b"host <computer>\n")


if __name__ == "__main__":
    unittest.main()

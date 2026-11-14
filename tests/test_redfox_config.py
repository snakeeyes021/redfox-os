"""redfox-config setup: plain configs (file, pipe, URL, paste) work as before, and an
age-encrypted config is decrypted after its passphrase (no temporary files), with a retry.

    python3 -m unittest tests.test_redfox_config

The encrypted cases need `age` on PATH (the image has it) and are skipped without it.
The fixtures' passphrase is "test passphrase".
"""

import argparse
import importlib.machinery
import importlib.util
import io
import os
import shutil
import stat
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "files" / "system" / "usr" / "bin" / "redfox-config"
FIXTURES = ROOT / "tests" / "fixtures" / "redfox-config"
PASSPHRASE = "test passphrase"
PLAIN = "nordvpn:\n  token: plain-test-token\nmachines:\n  test-machine:\n    hostname: testbox\n"
DECRYPTED = "nordvpn:\n  token: encrypted-test-token\nmachines:\n  test-machine:\n    hostname: testbox\n"

loader = importlib.machinery.SourceFileLoader("redfox_config", str(SCRIPT))
spec = importlib.util.spec_from_loader("redfox_config", loader)
rc = importlib.util.module_from_spec(spec)
loader.exec_module(rc)

HAVE_AGE = shutil.which("age") is not None


class FakeStdin:
    def __init__(self, data=b"", tty=False):
        self.buffer = io.BytesIO(data)
        self.tty = tty

    def isatty(self):
        return self.tty


class Response:
    def __init__(self, data):
        self.data = data

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class SetupBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.config = self.tmp / "redfox" / "config.yaml"
        for name, value in (("USER_CONFIG_DIR", self.config.parent), ("USER_CONFIG_PATH", self.config)):
            patcher = unittest.mock.patch.object(rc, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        # No hardware lookups in the summary.
        patcher = unittest.mock.patch.object(rc, "get_hardware_identifiers", return_value=[])
        patcher.start()
        self.addCleanup(patcher.stop)

    def setup(self, source=None, stdin=None, inputs=None, passphrases=None):
        """Run `redfox-config setup [source]`; returns (output, exit code or None)."""
        stdin = stdin or FakeStdin(tty=True)
        out = io.StringIO()
        code = None
        patches = [unittest.mock.patch.object(rc.sys, "stdin", stdin)]
        if inputs is not None:
            patches.append(unittest.mock.patch("builtins.input", side_effect=list(inputs) + [EOFError()]))
        asked = []
        if passphrases is not None:
            def ask(prompt):
                asked.append(prompt)
                return passphrases.pop(0)
            patches.append(unittest.mock.patch.object(rc, "ask_passphrase", side_effect=ask))
        for p in patches:
            p.start()
        try:
            with redirect_stdout(out):
                rc.cmd_setup(argparse.Namespace(source=source))
        except SystemExit as e:
            code = e.code
        finally:
            for p in reversed(patches):
                p.stop()
        self.asked = asked
        return out.getvalue(), code

    def saved(self):
        return self.config.read_text(encoding="utf-8")

    def write(self, name, data):
        path = self.tmp / name
        path.write_bytes(data if isinstance(data, bytes) else data.encode())
        return path


class PlainConfigs(SetupBase):
    def test_file(self):
        out, code = self.setup(str(self.write("cfg.yaml", PLAIN)))
        self.assertIsNone(code, out)
        self.assertEqual(self.saved(), PLAIN)
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o600)

    def test_quoted_path_from_a_drop(self):
        path = self.write("my cfg.yaml", PLAIN)
        out, code = self.setup(inputs=[f"'{path}'"])
        self.assertIsNone(code, out)
        self.assertEqual(self.saved(), PLAIN)

    def test_pipe(self):
        out, code = self.setup(stdin=FakeStdin(PLAIN.encode()))
        self.assertIsNone(code, out)
        self.assertEqual(self.saved(), PLAIN)

    def test_url(self):
        with unittest.mock.patch.object(rc.urllib.request, "urlopen", return_value=Response(PLAIN.encode())):
            out, code = self.setup("https://example.com/config.yaml")
        self.assertIsNone(code, out)
        self.assertEqual(self.saved(), PLAIN)

    def test_plain_http_is_refused(self):
        out, code = self.setup("http://example.com/config.yaml")
        self.assertEqual(code, 1)
        self.assertFalse(self.config.exists())

    def test_paste_with_a_blank_line_inside(self):
        lines = PLAIN.splitlines()
        out, code = self.setup(inputs=lines[:2] + [""] + lines[2:] + ["", ""])
        self.assertIsNone(code, out)
        self.assertEqual(self.saved(), "\n".join(lines[:2] + [""] + lines[2:]) + "\n")

    def test_skip(self):
        out, code = self.setup(inputs=[""])
        self.assertIsNone(code)
        self.assertIn("skipped", out)
        self.assertFalse(self.config.exists())

    def test_invalid_yaml_keeps_the_old_config(self):
        self.config.parent.mkdir(parents=True)
        self.config.write_text(PLAIN)
        out, code = self.setup(str(self.write("bad.yaml", "just a string")))
        self.assertEqual(code, 1)
        self.assertEqual(self.saved(), PLAIN)

    def test_binary_junk_is_refused(self):
        out, code = self.setup(str(self.write("junk.bin", b"\xff\xfe\x00junk")))
        self.assertEqual(code, 1)
        self.assertFalse(self.config.exists())

    def test_no_passphrase_asked_for_plain(self):
        self.setup(str(self.write("cfg.yaml", PLAIN)), passphrases=[])
        self.assertEqual(self.asked, [])


class Detection(unittest.TestCase):
    def test_age_headers(self):
        self.assertTrue(rc.is_encrypted((FIXTURES / "config.age").read_bytes()))
        self.assertTrue(rc.is_encrypted((FIXTURES / "config.age.asc").read_bytes()))
        self.assertTrue(rc.is_encrypted(b"\n  " + (FIXTURES / "config.age.asc").read_bytes()))
        self.assertFalse(rc.is_encrypted(PLAIN.encode()))
        self.assertFalse(rc.is_encrypted(b"age: 42\n"))


class FilePicker(SetupBase):
    def test_f_opens_the_picker_in_a_desktop_session(self):
        path = self.write("cfg.yaml", PLAIN)
        with unittest.mock.patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0"}), \
                unittest.mock.patch("shutil.which", return_value="/usr/bin/zenity"), \
                unittest.mock.patch.object(rc, "pick_file", return_value=str(path)) as pick:
            out, code = self.setup(inputs=["F"])
        pick.assert_called_once()
        self.assertIsNone(code, out)
        self.assertEqual(self.saved(), PLAIN)

    def test_cancelled_picker_changes_nothing(self):
        with unittest.mock.patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0"}), \
                unittest.mock.patch("shutil.which", return_value="/usr/bin/zenity"), \
                unittest.mock.patch.object(rc, "pick_file", return_value=""):
            out, code = self.setup(inputs=["f"])
        self.assertIsNone(code)
        self.assertFalse(self.config.exists())

    def test_no_picker_without_a_desktop(self):
        env = {k: v for k, v in os.environ.items() if k not in ("WAYLAND_DISPLAY", "DISPLAY")}
        with unittest.mock.patch.dict(os.environ, env, clear=True), \
                unittest.mock.patch.object(rc, "pick_file") as pick:
            out, code = self.setup(inputs=["F", "", ""])
        pick.assert_not_called()
        self.assertNotIn("choose a file", out)


@unittest.skipUnless(HAVE_AGE, "age isn't installed")
class EncryptedConfigs(SetupBase):
    def test_binary_file(self):
        out, code = self.setup(str(FIXTURES / "config.age"), passphrases=[PASSPHRASE])
        self.assertIsNone(code, out)
        self.assertEqual(self.saved(), DECRYPTED)
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o600)

    def test_armored_file(self):
        out, code = self.setup(str(FIXTURES / "config.age.asc"), passphrases=[PASSPHRASE])
        self.assertIsNone(code, out)
        self.assertEqual(self.saved(), DECRYPTED)

    def test_binary_pipe(self):
        out, code = self.setup(stdin=FakeStdin((FIXTURES / "config.age").read_bytes()), passphrases=[PASSPHRASE])
        self.assertIsNone(code, out)
        self.assertEqual(self.saved(), DECRYPTED)

    def test_url(self):
        data = (FIXTURES / "config.age").read_bytes()
        with unittest.mock.patch.object(rc.urllib.request, "urlopen", return_value=Response(data)):
            out, code = self.setup("https://example.com/config.age", passphrases=[PASSPHRASE])
        self.assertIsNone(code, out)
        self.assertEqual(self.saved(), DECRYPTED)

    def test_pasted_armor_ends_at_its_end_line(self):
        lines = (FIXTURES / "config.age.asc").read_text().splitlines()
        out, code = self.setup(inputs=lines + ["never read"], passphrases=[PASSPHRASE])
        self.assertIsNone(code, out)
        self.assertEqual(self.saved(), DECRYPTED)

    def test_wrong_passphrase_then_right(self):
        out, code = self.setup(str(FIXTURES / "config.age"), passphrases=["nope", PASSPHRASE])
        self.assertIsNone(code, out)
        self.assertIn("That passphrase is wrong. Try again.", out)
        self.assertEqual(len(self.asked), 2)
        self.assertEqual(self.saved(), DECRYPTED)

    def test_wrong_three_times_keeps_the_old_config(self):
        self.config.parent.mkdir(parents=True)
        self.config.write_text(PLAIN)
        out, code = self.setup(str(FIXTURES / "config.age"), passphrases=["a", "b", "c"])
        self.assertEqual(code, 1)
        self.assertIn("Configuration unchanged", out)
        self.assertEqual(self.saved(), PLAIN)
        self.assertFalse(list(self.config.parent.glob(".*.tmp")))

    def test_cancel_at_the_passphrase(self):
        out, code = self.setup(str(FIXTURES / "config.age"), passphrases=[""])
        self.assertIsNone(code)
        self.assertFalse(self.config.exists())

    def test_encrypted_to_a_key(self):
        out, code = self.setup(str(FIXTURES / "config-to-a-key.age"), passphrases=[PASSPHRASE])
        self.assertEqual(code, 1)
        self.assertIn("encrypted to a key, not a passphrase", out)
        self.assertFalse(self.config.exists())


PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 32
JPEG = b"\xff\xd8\xff\xe0" + b"\0" * 32


def b64(data):
    import base64
    return base64.b64encode(data).decode()


class ProfilePicture(unittest.TestCase):
    def test_png_and_jpeg(self):
        self.assertEqual(rc.decode_picture(b64(PNG)), (PNG, "png"))
        self.assertEqual(rc.decode_picture(b64(JPEG)), (JPEG, "jpg"))

    def test_data_url_and_wrapped_lines(self):
        text = b64(PNG)
        self.assertEqual(rc.decode_picture("data:image/png;base64," + text)[0], PNG)
        self.assertEqual(rc.decode_picture(text[:10] + "\n" + text[10:])[0], PNG)

    def test_refusals(self):
        for value, words in (("not base64!!", "valid base64"), (b64(b"GIF89a" + b"\0" * 8), "PNG or JPEG"),
                             (b64(PNG + b"\0" * rc.MAX_PICTURE_BYTES), "over 1 MB")):
            with self.assertRaises(ValueError) as cm:
                rc.decode_picture(value)
            self.assertIn(words, str(cm.exception))

    def test_absent_is_skipped(self):
        with unittest.mock.patch.object(rc, "set_account_picture") as setter:
            self.assertIsNone(rc.apply_profile_picture({}))
            self.assertIsNone(rc.apply_profile_picture({"profile_picture": ""}))
        setter.assert_not_called()

    def test_applied_through_accountsservice(self):
        seen = {}

        def setter(path):
            seen["data"] = path.read_bytes()
            seen["name"] = path.name
            seen["mode"] = stat.S_IMODE(path.stat().st_mode)

        with unittest.mock.patch.object(rc, "set_account_picture", side_effect=setter), \
                unittest.mock.patch.object(rc.os, "getuid", return_value=1000):
            line = rc.apply_profile_picture({"profile_picture": b64(JPEG)})
        self.assertIn("Set as your account picture", line)
        self.assertEqual(seen, {"data": JPEG, "name": "picture.jpg", "mode": 0o600})

    def test_bad_picture_is_reported_not_fatal(self):
        with unittest.mock.patch.object(rc, "set_account_picture") as setter:
            line = rc.apply_profile_picture({"profile_picture": "nope"})
        setter.assert_not_called()
        self.assertIn("Not applied", line)

    def test_accountsservice_failure_is_reported(self):
        with unittest.mock.patch.object(rc, "set_account_picture", side_effect=RuntimeError("denied")), \
                unittest.mock.patch.object(rc.os, "getuid", return_value=1000):
            self.assertIn("Not applied: denied", rc.apply_profile_picture({"profile_picture": b64(PNG)}))

    def test_not_as_root(self):
        with unittest.mock.patch.object(rc, "set_account_picture") as setter, \
                unittest.mock.patch.object(rc.os, "getuid", return_value=0):
            self.assertIn("not as root", rc.apply_profile_picture({"profile_picture": b64(PNG)}))
        setter.assert_not_called()

    def test_gdbus_calls(self):
        calls = []

        def run(cmd, **kwargs):
            calls.append(cmd)
            out = "(objectpath '/org/freedesktop/Accounts/User1000',)\n" if "FindUserByName" in cmd[-2] else "()\n"
            return unittest.mock.Mock(returncode=0, stdout=out, stderr="")

        with unittest.mock.patch.object(rc.subprocess, "run", side_effect=run):
            rc.set_account_picture(Path("/tmp/x/picture.png"))
        self.assertEqual(calls[1][calls[1].index("--object-path") + 1], "/org/freedesktop/Accounts/User1000")
        self.assertEqual(calls[1][-2:], ["org.freedesktop.Accounts.User.SetIconFile", "/tmp/x/picture.png"])


class SetupAppliesThePicture(SetupBase):
    def test_setup_prints_the_result(self):
        with unittest.mock.patch.object(rc, "set_account_picture") as setter, \
                unittest.mock.patch.object(rc.os, "getuid", return_value=1000):
            out, code = self.setup(str(self.write("cfg.yaml", PLAIN + f"profile_picture: {b64(PNG)}\n")))
        self.assertIsNone(code, out)
        setter.assert_called_once()
        self.assertIn("Profile picture : Set as your account picture.", out)

    def test_no_picture_no_line(self):
        with unittest.mock.patch.object(rc, "set_account_picture") as setter:
            out, code = self.setup(str(self.write("cfg.yaml", PLAIN)))
        setter.assert_not_called()
        self.assertNotIn("Profile picture", out)


MS_ACCOUNT = {"id": "a378f75c", "name": "Test One", "provider": "imap", "emailAddress": "test1@example.test",
              "settings": {"imap_host": "127.0.0.1", "imap_port": 3143, "imap_username": "test1"}}
MS_BLOB = b"v12" + bytes(range(40))
MS_TOKEN = bytes(range(64))


def ms_section():
    return {"accounts": [MS_ACCOUNT], "credentials": b64(MS_BLOB), "portal_token": b64(MS_TOKEN)}


class Mailspring(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.ms_config = self.tmp / "Mailspring" / "config.json"
        self.tokens = []
        patches = [
            unittest.mock.patch.object(rc, "MAILSPRING_CONFIG", self.ms_config),
            unittest.mock.patch.object(rc, "write_portal_token", side_effect=self.tokens.append),
            unittest.mock.patch.object(rc, "mailspring_running", return_value=False),
            unittest.mock.patch.object(rc.os, "getuid", return_value=1000),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def config(self):
        import json
        return json.loads(self.ms_config.read_text())

    def test_absent_is_skipped(self):
        self.assertIsNone(rc.apply_mailspring({}))
        self.assertEqual(self.tokens, [])
        self.assertFalse(self.ms_config.exists())

    def test_restores_accounts_logins_and_token(self):
        line = rc.apply_mailspring({"mailspring": ms_section()})
        self.assertIn("1 account(s) restored", line)
        self.assertEqual(self.tokens, [MS_TOKEN])
        star = self.config()["*"]
        self.assertEqual(star["accounts"], [MS_ACCOUNT])
        self.assertEqual(star["credentials"], {"type": "Buffer", "data": list(MS_BLOB)})
        self.assertEqual(stat.S_IMODE(self.ms_config.stat().st_mode), 0o600)

    def test_keeps_the_theme_settings_already_there(self):
        import json
        self.ms_config.parent.mkdir(parents=True)
        self.ms_config.write_text(json.dumps({"*": {"core": {"themes": ["redfox-adwaita"]}, "env": "production"}}))
        rc.apply_mailspring({"mailspring": ms_section()})
        star = self.config()["*"]
        self.assertEqual(star["core"], {"themes": ["redfox-adwaita"]})
        self.assertEqual(star["env"], "production")
        self.assertEqual(star["accounts"], [MS_ACCOUNT])

    def test_existing_accounts_are_left_alone(self):
        import json
        self.ms_config.parent.mkdir(parents=True)
        before = json.dumps({"*": {"accounts": [dict(MS_ACCOUNT, id="other")]}})
        self.ms_config.write_text(before)
        line = rc.apply_mailspring({"mailspring": ms_section()})
        self.assertIn("already has accounts", line)
        self.assertEqual(self.tokens, [])
        self.assertEqual(self.ms_config.read_text(), before)

    def test_not_while_mailspring_is_open(self):
        with unittest.mock.patch.object(rc, "mailspring_running", return_value=True):
            line = rc.apply_mailspring({"mailspring": ms_section()})
        self.assertIn("Mailspring is open", line)
        self.assertEqual(self.tokens, [])
        self.assertFalse(self.ms_config.exists())

    def test_incomplete_sections_are_refused(self):
        for broken, words in (
                ({"accounts": []}, "must list the accounts"),
                ({"accounts": [{"name": "x"}]}, "must list the accounts"),
                (dict(ms_section(), credentials="not base64!"), "must be base64"),
                (dict(ms_section(), portal_token=""), "needs both")):
            with self.subTest(words=words):
                line = rc.apply_mailspring({"mailspring": broken})
                self.assertIn(words, line)
        self.assertEqual(self.tokens, [])
        self.assertFalse(self.ms_config.exists())

    def test_keyring_failure_writes_nothing_else(self):
        with unittest.mock.patch.object(rc, "write_portal_token", side_effect=RuntimeError("the keyring is locked")):
            line = rc.apply_mailspring({"mailspring": ms_section()})
        self.assertIn("Not applied: the keyring is locked", line)
        self.assertFalse(self.ms_config.exists())

    def test_not_as_root(self):
        with unittest.mock.patch.object(rc.os, "getuid", return_value=0):
            self.assertIn("not as root", rc.apply_mailspring({"mailspring": ms_section()}))
        self.assertEqual(self.tokens, [])

    def test_export_then_apply_round_trip(self):
        import json
        self.ms_config.parent.mkdir(parents=True)
        full = dict(MS_ACCOUNT, syncState="ok", authedAt=1, metadata=[], __cls="Account")
        self.ms_config.write_text(json.dumps({"*": {"accounts": [full], "core": {},
                                                    "credentials": {"type": "Buffer", "data": list(MS_BLOB)}}}))
        with unittest.mock.patch.object(rc, "read_portal_token", return_value=MS_TOKEN):
            sec = rc.mailspring_section()
        self.assertEqual(sec, ms_section())
        self.ms_config.unlink()
        rc.apply_mailspring({"mailspring": sec})
        self.assertEqual(self.config()["*"]["accounts"], [MS_ACCOUNT])
        self.assertEqual(self.tokens, [MS_TOKEN])

    def test_export_needs_accounts_and_the_key(self):
        with self.assertRaises(RuntimeError):
            rc.mailspring_section()
        import json
        self.ms_config.parent.mkdir(parents=True)
        self.ms_config.write_text(json.dumps({"*": {"accounts": [MS_ACCOUNT],
                                                    "credentials": {"type": "Buffer", "data": [1]}}}))
        with unittest.mock.patch.object(rc, "read_portal_token", return_value=b""), \
                self.assertRaises(RuntimeError):
            rc.mailspring_section()

    def test_write_portal_token_replaces_the_old_one(self):
        calls = []

        def call(path, iface, method, args, reply):
            calls.append((path, method))
            return {"SearchItems": (["/old/item"], []), "Delete": ("/",), "OpenSession": (None, "/session/1"),
                    "CreateItem": ("/new/item", "/")}[method]

        real = Mailspring.real_write  # the real function; setUp replaces rc.write_portal_token
        with unittest.mock.patch.object(rc, "secret_call", side_effect=call):
            real(MS_TOKEN)
        self.assertEqual([m for _, m in calls], ["SearchItems", "Delete", "OpenSession", "CreateItem"])
        self.assertEqual(calls[1][0], "/old/item")

    def test_show_hides_the_secrets(self):
        cfg = {"mailspring": ms_section(), "profile_picture": b64(PNG)}
        out = io.StringIO()
        with unittest.mock.patch.object(rc, "USER_CONFIG_PATH", self.tmp / "c.yaml"), redirect_stdout(out):
            import yaml
            (self.tmp / "c.yaml").write_text(yaml.safe_dump(cfg))
            rc.cmd_show(None)
        self.assertNotIn(ms_section()["portal_token"], out.getvalue())
        self.assertNotIn(ms_section()["credentials"], out.getvalue())
        self.assertIn("(hidden,", out.getvalue())
        self.assertIn("(an image,", out.getvalue())


Mailspring.real_write = staticmethod(rc.write_portal_token)


class NoAge(SetupBase):
    def test_missing_age_is_a_clear_error(self):
        with unittest.mock.patch("shutil.which", return_value=None):
            out, code = self.setup(str(FIXTURES / "config.age"), passphrases=[PASSPHRASE])
        self.assertEqual(code, 1)
        self.assertIn("age isn't installed", out)
        self.assertEqual(self.asked, [], "no passphrase should be asked for when age is missing")
        self.assertFalse(self.config.exists())


class PictureEdges(unittest.TestCase):
    def test_binary_yaml_form(self):
        self.assertEqual(rc.decode_picture(PNG), (PNG, "png"))

    def test_far_too_big_is_refused_before_decoding(self):
        with unittest.mock.patch("base64.b64decode") as decode, self.assertRaises(ValueError) as cm:
            rc.decode_picture("A" * (rc.MAX_PICTURE_BYTES * 2))
        decode.assert_not_called()
        self.assertIn("over 1 MB", str(cm.exception))


if __name__ == "__main__":
    unittest.main()

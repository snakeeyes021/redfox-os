import base64
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import os
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "files" / "system" / "usr" / "libexec" / "redfox-t3code"

loader = importlib.machinery.SourceFileLoader("redfox_t3code", str(SCRIPT))
spec = importlib.util.spec_from_loader("redfox_t3code", loader)
t3 = importlib.util.module_from_spec(spec)
loader.exec_module(t3)

PAYLOAD = b"not really an AppImage"
DL = "https://github.com/pingdotgg/t3code/releases/download"


def release(tag, prerelease, published, files=None, digest=None):
    version = tag[1:]
    name = f"T3-Code-{version}-x86_64.AppImage"
    feed = "nightly-linux.yml" if "nightly" in tag else "latest-linux.yml"
    names = files if files is not None else [name, feed]
    return {
        "tag_name": tag, "prerelease": prerelease, "draft": False, "published_at": published,
        "assets": [{
            "name": n, "browser_download_url": f"{DL}/{tag}/{n}", "size": len(PAYLOAD),
            "digest": digest if n == name and digest is not None
            else "sha256:" + hashlib.sha256(PAYLOAD).hexdigest(),
        } for n in names],
    }


RELEASES = [
    release("v0.1.10-preview.20261111.4539", True, "2026-11-11T20:12:29Z",
            files=["T3-Code-0.1.10-preview.20261111.4539-x86_64.AppImage"]),
    release("v0.1.10-nightly.20261111.4529", True, "2026-11-11T15:48:32Z"),
    release("v0.1.9", False, "2026-11-11T11:33:49Z"),
    release("v0.1.9-nightly.20261111.4515", True, "2026-11-11T09:24:33Z"),
]


def feed_for(name, sha512=None):
    sha512 = sha512 or base64.b64encode(hashlib.sha512(PAYLOAD).digest()).decode()
    return f"version: x\nfiles:\n  - url: {name}\n    sha512: {sha512}\n".encode()


class TestRelease(unittest.TestCase):
    def test_nightly_skips_previews_and_stable(self):
        with unittest.mock.patch.object(t3, "fetch", return_value=json.dumps(RELEASES).encode()):
            rel, version = t3.newest_release("nightly")
        self.assertEqual(rel["tag_name"], "v0.1.10-nightly.20261111.4529")
        self.assertEqual(version, "0.1.10-nightly.20261111.4529")

    def test_stable_is_the_latest_release(self):
        with unittest.mock.patch.object(t3, "fetch", return_value=json.dumps(RELEASES[2]).encode()):
            rel, version = t3.newest_release("stable")
        self.assertEqual((rel["tag_name"], version), ("v0.1.9", "0.1.9"))

    def test_stable_refuses_a_prerelease(self):
        with unittest.mock.patch.object(t3, "fetch", return_value=json.dumps(RELEASES[1]).encode()), \
                self.assertRaises(SystemExit):
            t3.newest_release("stable")

    def test_asset_must_come_from_the_release(self):
        rel = release("v0.1.9", False, "x")
        rel["assets"][0]["browser_download_url"] = "https://example.com/T3-Code-0.1.9-x86_64.AppImage"
        with self.assertRaises(SystemExit):
            t3.asset(rel, "T3-Code-0.1.9-x86_64.AppImage")


class TestInstall(unittest.TestCase):
    def run_install(self, rel, feed, channel="stable"):
        """Install with GitHub, the download and Gear Lever faked; returns
        Gear Lever's calls and the exit (None if it finished)."""
        calls = []

        def fake_fetch(url, accept=None):
            if url.endswith("/releases/latest") or "/releases?" in url:
                return json.dumps(rel if url.endswith("latest") else [rel]).encode()
            return feed

        def fake_urlopen(req, timeout=None):
            return io.BytesIO(PAYLOAD)

        def fake_gearlever(*args, check=True):
            calls.append(args)
            res = unittest.mock.Mock(returncode=0)
            listed = [{"name": "T3 Code (Beta) (0.1.10-nightly.20261111.4529)", "path": "/home/u/AppImages/t3_code.appimage", "desktop_id": "t3_code.desktop"}]
            integrated = any(c[0] == "--integrate" for c in calls)
            res.stdout = json.dumps({"schema_version": 1, "installed": listed if integrated else []})
            return res

        with tempfile.TemporaryDirectory() as d, \
                unittest.mock.patch.dict(os.environ, {"XDG_STATE_HOME": d, "XDG_CACHE_HOME": d}), \
                unittest.mock.patch.object(t3, "fetch", fake_fetch), \
                unittest.mock.patch.object(t3.urllib.request, "urlopen", fake_urlopen), \
                unittest.mock.patch.object(t3, "gearlever", fake_gearlever), \
                unittest.mock.patch.object(t3, "ensure_gearlever"), \
                unittest.mock.patch.object(t3.os.path, "isfile", return_value=True), \
                redirect_stdout(io.StringIO()):
            try:
                t3.install(channel)
                code = None
            except SystemExit as e:
                code = e.code
            state = None
            if os.path.exists(os.path.join(d, "redfox", "t3code.json")):
                with open(os.path.join(d, "redfox", "t3code.json")) as f:
                    state = json.load(f)
            leftovers = [n for n in os.listdir(d) if n.startswith("redfox-t3code-")]
        return calls, code, state, leftovers

    def test_installs_and_follows_the_channel(self):
        rel = release("v0.1.10-nightly.20261111.4529", True, "x")
        calls, code, state, leftovers = self.run_install(
            rel, feed_for("T3-Code-0.1.10-nightly.20261111.4529-x86_64.AppImage"), "nightly")
        self.assertIsNone(code)
        self.assertEqual(leftovers, [])
        self.assertEqual(calls[1][0], "--integrate")
        self.assertEqual(calls[-1], (
            "--set-update-source", "/home/u/AppImages/t3_code.appimage", "--manager",
            "GithubUpdater", "repo=pingdotgg/t3code",
            "repo_filename=T3-Code-*-nightly.*-x86_64.AppImage", "allow_prereleases=true"))
        self.assertEqual(state["channel"], "nightly")

    def test_wrong_feed_checksum_runs_nothing(self):
        rel = release("v0.1.9", False, "x")
        calls, code, state, leftovers = self.run_install(
            rel, feed_for("T3-Code-0.1.9-x86_64.AppImage", sha512="AAAA"))
        self.assertIn("checksums", str(code))
        self.assertFalse(any(c[0] == "--integrate" for c in calls))
        self.assertIsNone(state)
        self.assertEqual(leftovers, [])

    def test_wrong_github_digest_runs_nothing(self):
        rel = release("v0.1.9", False, "x", digest="sha256:" + "0" * 64)
        calls, code, _state, _left = self.run_install(rel, feed_for("T3-Code-0.1.9-x86_64.AppImage"))
        self.assertIn("checksums", str(code))
        self.assertFalse(any(c[0] == "--integrate" for c in calls))

    def test_missing_checksum_runs_nothing(self):
        rel = release("v0.1.9", False, "x")
        calls, code, _state, _left = self.run_install(rel, b"version: x\nfiles: []\n")
        self.assertIn("no checksum", str(code))
        self.assertFalse(any(c[0] == "--integrate" for c in calls))


class TestRemove(unittest.TestCase):
    def test_url_handler_goes_only_with_its_appimage(self):
        with tempfile.TemporaryDirectory() as d, \
                unittest.mock.patch.dict(os.environ, {"XDG_DATA_HOME": d}), \
                unittest.mock.patch.object(t3.shutil, "which", return_value=None):
            apps = Path(d) / "applications"
            apps.mkdir()
            entry = apps / t3.T3_DESKTOP_ENTRY
            entry.write_text("[Desktop Entry]\nExec=/home/u/AppImages/t3_code_beta.appimage %U\n")
            t3.remove_url_handler(["/home/u/AppImages/t3_code_nightly.appimage"])
            self.assertTrue(entry.exists())
            t3.remove_url_handler(["/home/u/AppImages/t3_code_beta.appimage"])
            self.assertFalse(entry.exists())


if __name__ == "__main__":
    unittest.main()

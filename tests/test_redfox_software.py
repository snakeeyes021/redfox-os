import io
import json
import os
import subprocess
import tempfile
import unittest
import unittest.mock
import importlib.util
import importlib.machinery
from contextlib import redirect_stdout
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = ROOT / "files" / "system" / "usr" / "bin" / "redfox-software"
CATALOG_PATH = ROOT / "files" / "system" / "usr" / "share" / "redfox" / "software.yaml"
JUSTFILE = ROOT / "files" / "system" / "usr" / "share" / "ublue-os" / "just" / "60-custom.just"

loader = importlib.machinery.SourceFileLoader("redfox_software", str(CLI_PATH))
spec = importlib.util.spec_from_loader("redfox_software", loader)
rs = importlib.util.module_from_spec(spec)
loader.exec_module(rs)

# What each `ujust install-<pack>` installed before the lists moved into the
# catalog, resolved through the recipe dependencies (just runs each once).
# Non-Flatpak items use the catalog's recipe slugs.
TODAY = {
    "ai": ['com.jeffser.Alpaca', 't3code'],
    "audio": ['info.puredata.Pd', 'net.purrdata.PurrData', 'net.sourceforge.VMPK', 'org.ardour.Ardour', 'org.audacityteam.Audacity', 'org.pipewire.Helvum', 'soundthread', 'tech.redfoxlabs.Pianola'],
    "basic": ['org.gnome.Calendar', 'org.gnome.Contacts', 'org.gnome.Maps', 'org.gnome.Snapshot', 'org.gnome.Weather', 'org.gnome.World.PikaBackup', 'org.gnome.clocks'],
    "bluefin-dx": ['de.leopoldluley.Clapgrep', 'io.github.getnf.embellish', 'io.github.ronniedroid.concessio', 'me.iepure.devtoolbox', 'org.freedesktop.Bustle', 'org.pipewire.Helvum'],
    "comms": ['dev.vencord.Vesktop', 'org.signal.Signal'],
    "compatibility": ['com.usebottles.bottles'],
    "creative": ['ch.theologeek.Manuskript', 'com.github.unrud.VideoDownloader', 'com.obsproject.Studio', 'com.orama_interactive.Pixelorama', 'info.puredata.Pd', 'io.github.wartybix.Constrict', 'net.pixieditor.PixiEditor', 'net.purrdata.PurrData', 'net.sourceforge.VMPK', 'nl.hjdskes.gcolor3', 'org.ardour.Ardour', 'org.audacityteam.Audacity', 'org.blender.Blender', 'org.bunkus.mkvtoolnix-gui', 'org.cvfosammmm.Setzer', 'org.darktable.Darktable', 'org.frescobaldi.Frescobaldi', 'org.gimp.GIMP', 'org.gnome.gitlab.YaLTeR.VideoTrimmer', 'org.inkscape.Inkscape', 'org.kde.digikam', 'org.kde.kdenlive', 'org.kde.krita', 'org.musescore.MuseScore', 'org.pipewire.Helvum', 'soundthread', 'tech.redfoxlabs.Pianola'],
    "daily": ['com.github.geigi.cozy', 'com.github.johnfactotum.Foliate', 'com.spotify.Client', 'dev.geopjr.Tuba', 'io.gitlab.news_flash.NewsFlash', 'org.gnome.Music'],
    "dev": ['ca.desrt.dconf-editor', 'io.podman_desktop.PodmanDesktop', 'org.gnome.Builder', 'org.gnome.dspy', 're.sonny.Workbench', 'zed'],
    "dewy": ['app.drey.Warp', 'be.alexandervanhee.gradia', 'com.bambulab.BambuStudio', 'com.brave.Browser', 'com.dropbox.Client', 'com.slack.Slack', 'com.spotify.Client', 'dev.vencord.Vesktop', 'net.cozic.joplin_desktop', 'net.pixieditor.PixiEditor', 'org.gnome.SimpleScan', 'org.libreoffice.LibreOffice', 'org.signal.Signal', 'org.texstudio.TeXstudio', 'org.videolan.VLC', 'texlive', 'zed'],
    "gnome-dev": ['org.gnome.Builder', 're.sonny.Workbench'],
    "graphics": ['com.orama_interactive.Pixelorama', 'net.pixieditor.PixiEditor', 'nl.hjdskes.gcolor3', 'org.blender.Blender', 'org.gimp.GIMP', 'org.inkscape.Inkscape', 'org.kde.krita'],
    "matt": ['antigravity-cli', 'app.drey.Warp', 'be.alexandervanhee.gradia', 'ca.desrt.dconf-editor', 'ch.theologeek.Manuskript', 'com.getmailspring.Mailspring', 'com.github.geigi.cozy', 'com.github.johnfactotum.Foliate', 'com.github.unrud.VideoDownloader', 'com.jeffser.Alpaca', 'com.obsproject.Studio', 'com.orama_interactive.Pixelorama', 'com.spotify.Client', 'com.usebottles.bottles', 'de.leopoldluley.Clapgrep', 'dev.geopjr.Tuba', 'dev.vencord.Vesktop', 'info.puredata.Pd', 'io.github.getnf.embellish', 'io.github.ronniedroid.concessio', 'io.github.wartybix.Constrict', 'io.gitlab.news_flash.NewsFlash', 'io.podman_desktop.PodmanDesktop', 'me.iepure.devtoolbox', 'net.cozic.joplin_desktop', 'net.pixieditor.PixiEditor', 'net.purrdata.PurrData', 'net.sourceforge.VMPK', 'nl.hjdskes.gcolor3', 'org.ardour.Ardour', 'org.audacityteam.Audacity', 'org.blender.Blender', 'org.bunkus.mkvtoolnix-gui', 'org.cvfosammmm.Setzer', 'org.darktable.Darktable', 'org.freedesktop.Bustle', 'org.frescobaldi.Frescobaldi', 'org.gimp.GIMP', 'org.gnome.Builder', 'org.gnome.Calendar', 'org.gnome.Contacts', 'org.gnome.Maps', 'org.gnome.Music', 'org.gnome.SimpleScan', 'org.gnome.Snapshot', 'org.gnome.Weather', 'org.gnome.World.PikaBackup', 'org.gnome.clocks', 'org.gnome.dspy', 'org.gnome.gitlab.YaLTeR.VideoTrimmer', 'org.inkscape.Inkscape', 'org.kde.digikam', 'org.kde.kdenlive', 'org.kde.krita', 'org.libreoffice.LibreOffice', 'org.musescore.MuseScore', 'org.pipewire.Helvum', 'org.signal.Signal', 're.sonny.Workbench', 'soundthread', 't3code', 'tech.redfoxlabs.Pianola', 'tech.redfoxlabs.Thirties', 'zed'],
    "normie": ['app.drey.Warp', 'be.alexandervanhee.gradia', 'com.getmailspring.Mailspring', 'com.github.geigi.cozy', 'com.github.johnfactotum.Foliate', 'com.spotify.Client', 'dev.geopjr.Tuba', 'dev.vencord.Vesktop', 'io.gitlab.news_flash.NewsFlash', 'net.cozic.joplin_desktop', 'org.gnome.Calendar', 'org.gnome.Contacts', 'org.gnome.Maps', 'org.gnome.Music', 'org.gnome.SimpleScan', 'org.gnome.Snapshot', 'org.gnome.Weather', 'org.gnome.World.PikaBackup', 'org.gnome.clocks', 'org.libreoffice.LibreOffice', 'org.signal.Signal'],
    "notation": ['org.frescobaldi.Frescobaldi', 'org.musescore.MuseScore'],
    "photos": ['org.darktable.Darktable', 'org.kde.digikam'],
    "productivity": ['app.drey.Warp', 'be.alexandervanhee.gradia', 'com.getmailspring.Mailspring', 'net.cozic.joplin_desktop', 'org.gnome.SimpleScan', 'org.libreoffice.LibreOffice'],
    "redfox-app-fleet": ['tech.redfoxlabs.Pianola', 'tech.redfoxlabs.Thirties'],
    "video": ['com.github.unrud.VideoDownloader', 'com.obsproject.Studio', 'io.github.wartybix.Constrict', 'org.bunkus.mkvtoolnix-gui', 'org.gnome.gitlab.YaLTeR.VideoTrimmer', 'org.kde.kdenlive'],
    "writing": ['ch.theologeek.Manuskript', 'org.cvfosammmm.Setzer'],
}

INSTALLED = {"org.gnome.clocks", "org.signal.Signal", "tech.redfoxlabs.Pianola"}


def fake_run(installed=INSTALLED, recipes_installed=()):
    """Stand-in for subprocess.run: answers `flatpak list` and recipe checks."""
    calls = []

    def run(argv, *args, **kwargs):
        calls.append(list(argv))
        if argv[:2] == ["flatpak", "list"]:
            out = "".join(f"{a}\n" for a in sorted(installed))
            return subprocess.CompletedProcess(argv, 0, stdout=out, stderr="")
        if argv[0] == "bash":
            ok = any(r in argv[-1] for r in recipes_installed)
            return subprocess.CompletedProcess(argv, 0 if ok else 1, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {argv}")

    run.calls = calls
    return run


class TestCatalog(unittest.TestCase):
    def setUp(self):
        self.catalog = rs.load_catalog(CATALOG_PATH)
        with open(CATALOG_PATH, encoding="utf-8") as f:
            self.raw = yaml.safe_load(f)

    def test_no_duplicate_ids(self):
        item_ids = [i["id"] for i in self.raw["items"]]
        pack_ids = [p["id"] for p in self.raw["packs"]]
        self.assertEqual(len(item_ids), len(set(item_ids)))
        self.assertEqual(len(pack_ids), len(set(pack_ids)))
        self.assertFalse(set(item_ids) & set(pack_ids))
        for pack in self.raw["packs"]:
            own = pack.get("items", [])
            self.assertEqual(len(own), len(set(own)), pack["id"])

    def test_every_pack_resolves(self):
        for pack in self.catalog.packs:
            items = self.catalog.resolve(pack["id"])
            self.assertTrue(items, pack["id"])
            for iid in items:
                self.assertIn(iid, self.catalog.items)

    def test_every_item_is_used(self):
        used = {i for p in self.catalog.packs for i in p["items"]}
        self.assertEqual(used, set(self.catalog.items))

    def test_items_are_complete(self):
        for iid, item in self.catalog.items.items():
            self.assertIn(item["kind"], rs.KINDS)
            self.assertTrue(item["name"].strip(), iid)
            self.assertTrue(item["summary"].strip(), iid)
            self.assertNotIn("\n", item["summary"].strip(), iid)
            if item["kind"] in ("flatpak", "redfox-app"):
                self.assertRegex(iid, r"^[A-Za-z][\w-]*(\.[\w-]+)+$")
            else:
                self.assertRegex(iid, r"^[a-z0-9-]+$")

    def test_bundles_match_the_old_recipes(self):
        for pack_id, expected in TODAY.items():
            self.assertEqual(sorted(self.catalog.resolve(pack_id)), sorted(expected), pack_id)
        # The Gaming and Hardware packs are new, built from Bazzite's own
        # recipes, and so is the AI pack; every other pack replaced an
        # install-* recipe.
        self.assertEqual(set(TODAY), {pid for pid, pack in self.catalog.pack_by_id.items()
                                      if pack["section"] in ("packs", "dev")})

    def test_hidden_packs(self):
        hidden = {p["id"] for p in self.catalog.packs if p["hidden"]}
        self.assertEqual(hidden, {"matt", "dewy", "normie"})

    def test_expand_mixes_packs_and_items(self):
        ids = self.catalog.expand(["comms", "zed", "org.signal.Signal"])
        self.assertEqual(ids, ["org.signal.Signal", "dev.vencord.Vesktop", "zed"])
        with self.assertRaises(rs.CatalogError):
            self.catalog.expand(["no-such-thing"])

    def test_include_cycles_are_rejected(self):
        data = {
            "items": [{"id": "a.b.C", "kind": "flatpak", "name": "C", "summary": "c"}],
            "packs": [
                {"id": "x", "name": "X", "description": "x", "includes": ["y"], "items": ["a.b.C"]},
                {"id": "y", "name": "Y", "description": "y", "includes": ["x"]},
            ],
        }
        with self.assertRaises(rs.CatalogError):
            rs.Catalog(data)

    def test_recipes_point_at_the_cli(self):
        text = JUSTFILE.read_text()
        for pack_id in TODAY:
            self.assertIn(f"install-{pack_id}:\n    /usr/bin/redfox-software install {pack_id}\n", text)
        self.assertNotIn("flatpak install -y flathub \\", text)


class TestList(unittest.TestCase):
    def setUp(self):
        self.catalog = rs.load_catalog(CATALOG_PATH)

    def test_list_json_contract(self):
        run = fake_run(recipes_installed=("SoundThread",))
        with unittest.mock.patch.object(rs.subprocess, "run", run), \
                unittest.mock.patch.dict(os.environ, {"REDFOX_SOFTWARE_CATALOG": str(CATALOG_PATH),
                                                      "REDFOX_GPU_VENDORS": "nvidia"}):
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(rs.main(["list", "--json"]), 0)
        data = json.loads(buf.getvalue())

        flatpak_lists = [c for c in run.calls if c[:2] == ["flatpak", "list"]]
        self.assertEqual(flatpak_lists, [["flatpak", "list", "--app", "--columns=application"]])

        self.assertEqual(set(data), {"version", "packs"})
        self.assertEqual(data["version"], 1)
        self.assertEqual([p["id"] for p in data["packs"]], [p["id"] for p in self.catalog.packs])
        seen = {}
        for pack in data["packs"]:
            self.assertEqual(set(pack), {"id", "name", "description", "section", "hidden",
                                         "includes", "items"})
            self.assertIn(pack["section"], rs.SECTIONS)
            for key in ("id", "name", "description"):
                self.assertIsInstance(pack[key], str)
            self.assertIsInstance(pack["hidden"], bool)
            self.assertIsInstance(pack["includes"], list)
            for item in pack["items"]:
                self.assertEqual(set(item), {"id", "kind", "name", "summary", "installed", "icon",
                                             "restart", "choice"})
                self.assertIsInstance(item["restart"], bool)
                self.assertIn(item["kind"], ("flatpak", "redfox-app", "recipe"))
                self.assertIsInstance(item["installed"], bool)
                self.assertTrue(item["icon"] is None or isinstance(item["icon"], str))
                seen[item["id"]] = item

        self.assertTrue(seen["org.gnome.clocks"]["installed"])
        self.assertEqual(seen["org.gnome.clocks"]["icon"], "org.gnome.clocks")
        self.assertTrue(seen["tech.redfoxlabs.Pianola"]["installed"])
        self.assertFalse(seen["org.gnome.Maps"]["installed"])
        self.assertIsNone(seen["org.gnome.Maps"]["icon"])
        self.assertTrue(seen["soundthread"]["installed"])
        self.assertFalse(seen["zed"]["installed"])
        self.assertIsNone(seen["zed"]["icon"])
        self.assertIsNone(seen["zed"]["choice"])
        self.assertEqual(seen["t3code"]["choice"], {
            "name": "Channel", "current": None,
            "options": [{"id": "stable", "name": "Stable"}, {"id": "nightly", "name": "Nightly"}]})
        self.assertTrue(next(p for p in data["packs"] if p["id"] == "matt")["hidden"])
        self.assertEqual(next(p for p in data["packs"] if p["id"] == "creative")["items"], [])

    def test_sections(self):
        sections = {p["id"]: p["section"] for p in self.catalog.packs}
        self.assertEqual(sections["basic"], "packs")
        for pack_id in ("dev", "gnome-dev", "bluefin-dx"):
            self.assertEqual(sections[pack_id], "dev")
        self.assertEqual(sections["gaming"], "gaming")
        self.assertEqual(sections["hardware"], "hardware")
        with self.assertRaises(rs.CatalogError):
            rs.Catalog({"items": [], "packs": [
                {"id": "p", "name": "P", "description": "d", "section": "nowhere"}]})

    def test_gpu_items_only_listed_with_that_gpu(self):
        def listed(vendors):
            with unittest.mock.patch.object(rs.subprocess, "run", fake_run()), \
                    unittest.mock.patch.dict(os.environ, {"REDFOX_GPU_VENDORS": vendors}):
                data = rs.list_packs(self.catalog)
            gaming = next(p for p in data["packs"] if p["id"] == "gaming")
            return {i["id"] for i in gaming["items"]}
        on_nvidia, on_amd = listed("nvidia intel"), listed("amd")
        self.assertIn("proton-dlss-upgrade", on_nvidia)
        self.assertNotIn("proton-fsr4-upgrade", on_nvidia)
        self.assertIn("proton-fsr4-upgrade", on_amd)
        self.assertIn("proton-fsr4-rdna3-upgrade", on_amd)
        self.assertNotIn("proton-dlss-upgrade", on_amd)
        with self.assertRaises(rs.CatalogError):
            rs.Catalog({"items": [{"id": "x", "kind": "flatpak", "name": "X",
                                   "summary": "s", "gpu": "voodoo"}], "packs": []})

    def test_version(self):
        buf = io.StringIO()
        with redirect_stdout(buf), self.assertRaises(SystemExit) as cm:
            rs.main(["--version"])
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(buf.getvalue().strip(), f"redfox-software {rs.VERSION}")


class FakeFlatpak:
    """Fakes flatpak list/install/uninstall for the install and remove paths."""

    def __init__(self, installed, broken=()):
        self.installed = set(installed)
        self.broken = set(broken)
        self.commands = []

    def run(self, argv, *args, **kwargs):
        if argv[:2] == ["flatpak", "list"]:
            out = "".join(f"{a}\n" for a in sorted(self.installed))
            return subprocess.CompletedProcess(argv, 0, stdout=out, stderr="")
        if argv[0] == "bash":
            return subprocess.CompletedProcess(argv, 1, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {argv}")

    def popen(self, argv, *args, **kwargs):
        self.commands.append(list(argv))
        lines, status = [], 0
        if argv[:2] == ["flatpak", "install"]:
            apps = argv[6:]
            if self.broken & set(apps):
                lines.append(f"error: Nothing matches {sorted(self.broken & set(apps))[0]} in remote flathub")
                status = 1
            else:
                for a in apps:
                    lines.append(f"Installing {a}")
                    self.installed.add(a)
        elif argv[:2] == ["flatpak", "uninstall"]:
            for a in argv[4:]:
                lines.append(f"Uninstalling {a}")
                self.installed.discard(a)
        proc = unittest.mock.Mock()
        proc.stdout = iter(line + "\n" for line in lines)
        proc.wait.return_value = status
        return proc


class TestInstallRemove(unittest.TestCase):
    def setUp(self):
        self.catalog = rs.load_catalog(CATALOG_PATH)

    def events(self, fake, verb, ids):
        buf = io.StringIO()
        with unittest.mock.patch.object(rs.subprocess, "run", fake.run), \
                unittest.mock.patch.object(rs.subprocess, "Popen", fake.popen), \
                redirect_stdout(buf):
            status = rs.apply(self.catalog, verb, ids, True)
        return status, [json.loads(line) for line in buf.getvalue().splitlines()]

    def test_install_pack_in_one_flatpak_call(self):
        fake = FakeFlatpak({"org.signal.Signal"})
        status, events = self.events(fake, "install", ["comms", "photos"])
        self.assertEqual(status, 0)
        self.assertEqual(fake.commands, [[
            "flatpak", "install", "--system", "--noninteractive", "-y", "flathub",
            "dev.vencord.Vesktop", "org.kde.digikam", "org.darktable.Darktable",
        ]])
        done = {e["id"]: e["ok"] for e in events if e["event"] == "done"}
        self.assertEqual(done, {
            "org.signal.Signal": True, "dev.vencord.Vesktop": True,
            "org.kde.digikam": True, "org.darktable.Darktable": True,
        })
        logs = [e for e in events if e["event"] == "log" and e["line"].startswith("Installing ")]
        self.assertEqual([e["id"] for e in logs], [e["line"].split()[1] for e in logs])
        self.assertEqual(events[-1], {"event": "finished", "ok": True})
        for e in events:
            self.assertIn(e["event"], ("start", "log", "done", "finished"))

    def test_one_bad_app_does_not_block_the_rest(self):
        fake = FakeFlatpak(set(), broken={"org.kde.digikam"})
        status, events = self.events(fake, "install", ["photos"])
        self.assertEqual(status, 1)
        done = {e["id"]: e["ok"] for e in events if e["event"] == "done"}
        self.assertEqual(done, {"org.kde.digikam": False, "org.darktable.Darktable": True})
        self.assertEqual(events[-1], {"event": "finished", "ok": False})

    def test_remove(self):
        fake = FakeFlatpak({"org.kde.digikam"})
        status, events = self.events(fake, "remove", ["photos"])
        self.assertEqual(status, 0)
        self.assertEqual(fake.commands, [["flatpak", "uninstall", "--noninteractive", "-y", "org.kde.digikam"]])
        self.assertNotIn("org.kde.digikam", fake.installed)

    def test_unknown_id_exits_before_doing_anything(self):
        with unittest.mock.patch.dict(os.environ, {"REDFOX_SOFTWARE_CATALOG": str(CATALOG_PATH)}), \
                unittest.mock.patch.object(rs.subprocess, "Popen") as popen, \
                redirect_stdout(io.StringIO()), unittest.mock.patch("sys.stderr", io.StringIO()):
            self.assertEqual(rs.main(["install", "--json", "nope"]), 2)
        popen.assert_not_called()

    def test_recipe_install_and_remove(self):
        with tempfile.TemporaryDirectory() as d:
            marker = Path(d) / "installed"
            catalog = rs.Catalog({
                "items": [{
                    "id": "thing", "kind": "recipe", "name": "Thing", "summary": "t",
                    "install": f"echo hello; touch '{marker}'",
                    "remove": f"rm -f '{marker}'",
                    "check": f"test -e '{marker}'",
                }],
                "packs": [{"id": "p", "name": "P", "description": "p", "items": ["thing"]}],
            })
            with unittest.mock.patch.object(rs, "installed_flatpaks", return_value=set()):
                for verb, exists in (("install", True), ("remove", False)):
                    buf = io.StringIO()
                    with redirect_stdout(buf):
                        self.assertEqual(rs.apply(catalog, verb, ["p"], True), 0)
                    events = [json.loads(line) for line in buf.getvalue().splitlines()]
                    self.assertEqual(marker.exists(), exists)
                    self.assertIn({"event": "done", "id": "thing", "ok": True}, events)
                    if verb == "install":
                        self.assertIn({"event": "log", "id": "thing", "line": "hello"}, events)

    def choice_catalog(self, d):
        out = Path(d) / "chosen"
        return out, rs.Catalog({
            "items": [{
                "id": "thing", "kind": "recipe", "name": "Thing", "summary": "t",
                "install": f"echo \"$REDFOX_CHOICE\" > '{out}'",
                "remove": f"rm -f '{out}'",
                "check": f"test -e '{out}'",
                "choice": {"name": "Channel", "current": f"cat '{out}'",
                           "options": [{"id": "stable", "name": "Stable"},
                                       {"id": "nightly", "name": "Nightly"}]},
            }],
            "packs": [{"id": "p", "name": "P", "description": "p", "items": ["thing"]}],
        })

    def test_choice_given_default_and_current(self):
        for given, expected in (({"thing": "nightly"}, "nightly"), ({}, "stable")):
            with tempfile.TemporaryDirectory() as d:
                out, catalog = self.choice_catalog(d)
                with unittest.mock.patch.object(rs, "installed_flatpaks", return_value=set()):
                    buf = io.StringIO()
                    with redirect_stdout(buf):
                        self.assertEqual(rs.apply(catalog, "install", ["p"], True, given), 0)
                    self.assertEqual(out.read_text().strip(), expected)
                    events = [json.loads(line) for line in buf.getvalue().splitlines()]
                    name = expected.capitalize()
                    self.assertIn({"event": "log", "id": "thing", "line": f"Channel: {name}"}, events)
                    listed = rs.list_packs(catalog)["packs"][0]["items"][0]
                    self.assertEqual(listed["choice"]["current"], expected)

    def test_choice_is_asked_in_a_terminal(self):
        with tempfile.TemporaryDirectory() as d:
            out, catalog = self.choice_catalog(d)
            with unittest.mock.patch.object(rs, "installed_flatpaks", return_value=set()), \
                    unittest.mock.patch.object(rs.sys.stdin, "isatty", return_value=True), \
                    unittest.mock.patch("builtins.input", side_effect=["9", "2"]), \
                    unittest.mock.patch.object(rs.subprocess, "run", wraps=rs.subprocess.run), \
                    redirect_stdout(io.StringIO()):
                self.assertEqual(rs.apply(catalog, "install", ["p"], False), 0)
            self.assertEqual(out.read_text().strip(), "nightly")

    def test_bad_choices_are_rejected(self):
        catalog = self.catalog
        self.assertEqual(rs.parse_choices(catalog, ["t3code=nightly"]), {"t3code": "nightly"})
        for bad in ("t3code=beta", "zed=stable", "t3code", "nope=stable"):
            with self.assertRaises(rs.CatalogError, msg=bad):
                rs.parse_choices(catalog, [bad])
        with self.assertRaises(rs.CatalogError):
            rs.Catalog({"items": [{"id": "a.b.C", "kind": "flatpak", "name": "C", "summary": "c",
                                   "choice": {"name": "X", "options": [{"id": "a", "name": "A"}]}}]})

    def test_catalog_env_override(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "software.yaml"
            path.write_text(yaml.safe_dump({
                "items": [{"id": "a.b.C", "kind": "flatpak", "name": "C", "summary": "c"}],
                "packs": [{"id": "p", "name": "P", "description": "p", "items": ["a.b.C"]}],
            }))
            with unittest.mock.patch.dict(os.environ, {"REDFOX_SOFTWARE_CATALOG": str(path)}):
                self.assertEqual(list(rs.load_catalog().pack_by_id), ["p"])


if __name__ == "__main__":
    unittest.main()

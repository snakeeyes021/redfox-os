import importlib.machinery
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYSTEM = ROOT / "files" / "system"
CLI_PATH = SYSTEM / "usr" / "bin" / "redfox-actions"
ACTION_HELPER = SYSTEM / "usr" / "libexec" / "redfox-system-action"
DEDUP = SYSTEM / "usr" / "libexec" / "redfox-dedup"
TERMINAL = SYSTEM / "usr" / "bin" / "redfox-terminal"
POLICY = SYSTEM / "usr" / "share" / "polkit-1" / "actions" / "tech.redfoxlabs.Hub.policy"

loader = importlib.machinery.SourceFileLoader("redfox_actions", str(CLI_PATH))
spec = importlib.util.spec_from_loader("redfox_actions", loader)
ra = importlib.util.module_from_spec(spec)
loader.exec_module(ra)


class Env:
    """A test computer: its graphics, whether it boots with UEFI, and
    whether Waydroid and Steam are there."""

    def __init__(self, gpus="", efi=True, waydroid_cfg=False, steam=True):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        (base / "home").mkdir()
        if efi:
            (base / "efi").mkdir()
        if waydroid_cfg:
            (base / "waydroid.cfg").write_text("")
        if steam:
            (base / "home" / ".local/share/Steam").mkdir(parents=True)
        self.env = {"REDFOX_GPU_VENDORS": gpus, "REDFOX_EFI_DIR": str(base / "efi"),
                    "REDFOX_WAYDROID_CFG": str(base / "waydroid.cfg"),
                    "HOME": str(base / "home")}

    def __enter__(self):
        self.patch = unittest.mock.patch.dict(os.environ, self.env)
        self.patch.start()
        self.which = unittest.mock.patch.object(ra.shutil, "which", lambda _name: "/usr/bin/x")
        self.which.start()
        return self

    def __exit__(self, *exc):
        self.which.stop()
        self.patch.stop()
        self.tmp.cleanup()


def listed(**kwargs):
    with Env(**kwargs):
        buf = io.StringIO()
        with redirect_stdout(buf):
            assert ra.main(["list", "--json"]) == 0
    return json.loads(buf.getvalue())


class TestList(unittest.TestCase):
    def test_contract(self):
        data = listed(gpus="nvidia")
        self.assertEqual(data["version"], 1)
        for a in data["actions"]:
            self.assertEqual(set(a), {"id", "group", "title", "subtitle", "button",
                                      "confirm", "done"})
            self.assertIn(a["group"], ra.GROUPS)
            if a["confirm"] is not None:
                self.assertEqual(set(a["confirm"]), {"heading", "body", "button"})
        ids = [a["id"] for a in data["actions"]]
        self.assertEqual(ids, [a["id"] for a in ra.ACTIONS])

    def test_nvidia_only_on_nvidia(self):
        self.assertIn("nvidia-flatpak", [a["id"] for a in listed(gpus="nvidia")["actions"]])
        self.assertNotIn("nvidia-flatpak", [a["id"] for a in listed(gpus="amd")["actions"]])

    def test_firmware_only_with_uefi(self):
        self.assertNotIn("firmware", [a["id"] for a in listed(efi=False)["actions"]])

    def test_reset_steam_only_with_steam(self):
        self.assertNotIn("reset-steam", [a["id"] for a in listed(steam=False)["actions"]])

    def test_the_destructive_ones_ask_first(self):
        by_id = {a["id"]: a for a in listed()["actions"]}
        self.assertIsNotNone(by_id["reset-steam"]["confirm"])
        self.assertIsNotNone(by_id["firmware"]["confirm"])
        self.assertIsNone(by_id["restart-audio"]["confirm"])

    def test_waydroid_says_when_its_set_up_and_warns_on_nvidia(self):
        fresh = {a["id"]: a for a in listed(gpus="nvidia")["actions"]}["waydroid"]
        self.assertFalse(fresh["done"])
        self.assertIn("NVIDIA", fresh["subtitle"])
        self.assertNotIn("NVIDIA", {a["id"]: a for a in listed(gpus="amd")["actions"]}
                         ["waydroid"]["subtitle"])
        done = {a["id"]: a for a in listed(waydroid_cfg=True)["actions"]}["waydroid"]
        self.assertTrue(done["done"])


class TestRun(unittest.TestCase):
    def run_action(self, action_id, returncode=0, **env):
        calls = []

        def fake(argv, *args, **kwargs):
            calls.append((list(argv), kwargs))
            return subprocess.CompletedProcess(argv, returncode)

        with Env(**env), unittest.mock.patch.object(ra.subprocess, "run", fake):
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = ra.main(["run", action_id])
        # stderr first: Python can print a ResourceWarning there at any time
        # (another test's unclosed file being collected), and it mustn't
        # displace the action's own last line on stdout.
        return code, calls, err.getvalue() + out.getvalue()

    def test_restart_audio(self):
        code, calls, out = self.run_action("restart-audio")
        self.assertEqual(code, 0)
        self.assertEqual(calls[0][0], ["ujust", "restart-pipewire"])
        self.assertEqual(out.strip().splitlines()[-1], "Audio restarted")

    def test_stop_games_is_fine_when_nothing_was_running(self):
        code, _calls, _out = self.run_action("stop-games", returncode=1)
        self.assertEqual(code, 0)

    def test_failures_are_reported(self):
        code, _calls, out = self.run_action("restart-audio", returncode=3)
        self.assertEqual(code, 3)
        self.assertIn("didn't finish", out)

    def test_reset_steam_answers_the_prompt_and_keeps_steam_off_the_output(self):
        _code, calls, _out = self.run_action("reset-steam")
        argv, kwargs = calls[0]
        self.assertEqual(argv, ["ujust", "fix-reset-steam"])
        self.assertEqual(kwargs["input"], "\n")
        self.assertEqual(kwargs["stdout"], subprocess.DEVNULL)

    def test_waydroid_runs_the_root_half_through_pkexec(self):
        with unittest.mock.patch.object(ra, "waydroid_menu_entry", return_value=0) as menu:
            code, calls, _out = self.run_action("waydroid")
        self.assertEqual(code, 0)
        self.assertEqual(calls[0][0], ["pkexec", ra.SYSTEM_HELPER, "waydroid-init"])
        menu.assert_called_once()

    def test_unavailable_actions_dont_run(self):
        code, calls, _out = self.run_action("nvidia-flatpak", gpus="amd")
        self.assertEqual(code, 1)
        self.assertEqual(calls, [])


class TestRootHelpers(unittest.TestCase):
    def test_action_helper_refuses_anything_else(self):
        for args in (["nope"], ["input-group"], ["input-group", "maybe"],
                     ["waydroid-init", "extra"], []):
            res = subprocess.run(["bash", str(ACTION_HELPER), *args], capture_output=True,
                                 text=True)
            self.assertEqual(res.returncode, 2, args)

    def test_input_group_needs_pkexec(self):
        env = {k: v for k, v in os.environ.items() if k != "PKEXEC_UID"}
        res = subprocess.run(["bash", str(ACTION_HELPER), "input-group", "add"],
                             capture_output=True, text=True, env=env)
        self.assertEqual(res.returncode, 1)
        self.assertIn("pkexec", res.stderr)

    def test_policy_points_at_the_action_helper(self):
        text = POLICY.read_text()
        self.assertIn('<action id="tech.redfoxlabs.hub.system-actions">', text)
        self.assertIn("/usr/libexec/redfox-system-action</annotate>", text)


class TestDedup(unittest.TestCase):
    def dedup(self, *args, size=None, uuid="1234-abcd"):
        env = dict(os.environ, REDFOX_DEDUP_UUID=uuid, REDFOX_DEDUP_ETC=tempfile.mkdtemp())
        if size is not None:
            env["REDFOX_DEDUP_SIZE"] = str(size)
        return subprocess.run(["bash", str(DEDUP), *args], capture_output=True, text=True,
                              env=env)

    def test_memory_follows_bazzites_sizing(self):
        tb = 1000 ** 4
        for size, mb in ((256 * 1000 ** 3, 512), (2 * tb, 1024), (2.6 * tb, 1536),
                         (20 * tb, 2048)):
            res = self.dedup("plan", "--json", size=int(size))
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertEqual(json.loads(res.stdout), {"uuid": "1234-abcd", "memory_mb": mb})

    def test_off_without_a_config(self):
        self.assertEqual(self.dedup("status").stdout.strip(), "off")

    def test_changes_need_root(self):
        if os.geteuid() == 0:
            self.skipTest("running as root")
        res = self.dedup("on", size=tb_bytes())
        self.assertEqual(res.returncode, 1)
        self.assertIn("root", res.stderr)

    def test_usage(self):
        self.assertEqual(self.dedup("sideways").returncode, 2)


def tb_bytes():
    return 1000 ** 4


class TestTerminal(unittest.TestCase):
    def test_status_per_switch(self):
        with tempfile.TemporaryDirectory() as home:
            env = dict(os.environ, HOME=home)
            Path(home, ".bashrc").write_text(
                "# >>> redfox-terminal tools >>>\nx\n# <<< redfox-terminal tools <<<\n")
            out = {w: subprocess.run(["bash", str(TERMINAL), w, "status"], env=env,
                                     capture_output=True, text=True).stdout.strip()
                   for w in ("prompt", "tools")}
        self.assertEqual(out, {"prompt": "off", "tools": "on"})


if __name__ == "__main__":
    unittest.main()

import importlib.machinery
import importlib.util
import io
import json
import subprocess
import unittest
import unittest.mock
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = ROOT / "files" / "system" / "usr" / "bin" / "redfox-toggles"
HELPER = ROOT / "files" / "system" / "usr" / "libexec" / "redfox-system-toggle"
POLICY = ROOT / "files" / "system" / "usr" / "share" / "polkit-1" / "actions" / "tech.redfoxlabs.Hub.policy"

loader = importlib.machinery.SourceFileLoader("redfox_toggles", str(CLI_PATH))
spec = importlib.util.spec_from_loader("redfox_toggles", loader)
rt = importlib.util.module_from_spec(spec)
loader.exec_module(rt)


def fake_run(answers):
    """subprocess.run stand-in: answers status commands from a dict of
    'joined argv' -> stdout, and records every call."""
    calls = []

    def run(argv, *args, **kwargs):
        calls.append(list(argv))
        out = answers.get(" ".join(argv))
        if out is None:
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(argv, 0, stdout=out, stderr="")

    run.calls = calls
    return run


class TestToggles(unittest.TestCase):
    def test_ids_groups_and_fields(self):
        ids = [t["id"] for t in rt.TOGGLES]
        self.assertEqual(len(ids), len(set(ids)))
        for t in rt.TOGGLES:
            self.assertIn(t["group"], ("terminal", "services", "storage", "sound"))
            for key in ("title", "subtitle", "status", "on_tokens"):
                self.assertTrue(t.get(key), (t["id"], key))
            if not t["system"]:
                self.assertTrue(t.get("on") and t.get("off"), t["id"])

    def test_list_reads_status_tokens(self):
        run = fake_run({
            "ujust tailscale status": "enable\n",
            "ujust ssh status": "start\n",            # running, not on at boot: off
            "ujust wol status": "force-enable\n",
            "systemctl --user is-enabled midikeep.service": "disabled\n",
            "ujust setup-virtual-channels status": "create\n",
        })
        with unittest.mock.patch.object(rt.subprocess, "run", run):
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(rt.main(["list", "--json"]), 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["version"], 1)
        state = {t["id"]: t["on"] for t in data["toggles"]}
        self.assertEqual([t["id"] for t in data["toggles"]], [t["id"] for t in rt.TOGGLES])
        self.assertIs(state["tailscale"], True)
        self.assertIs(state["ssh"], False)
        self.assertIs(state["wake-on-lan"], True)
        self.assertIs(state["midikeep"], False)
        self.assertIs(state["virtual-channels"], True)
        self.assertIsNone(state["cockpit"])   # no answer: unknown
        for t in data["toggles"]:
            self.assertEqual(set(t), {"id", "group", "title", "subtitle", "system", "on"})

    def test_system_toggles_go_through_pkexec_and_the_helper(self):
        run = fake_run({})
        with unittest.mock.patch.object(rt.subprocess, "run", run):
            self.assertEqual(rt.main(["on", "tailscale"]), 0)
            self.assertEqual(rt.main(["off", "snapshots"]), 0)
        self.assertEqual(run.calls, [
            ["pkexec", rt.SYSTEM_HELPER, "tailscale", "on"],
            ["pkexec", rt.SYSTEM_HELPER, "snapshots", "off"],
        ])

    def test_user_toggles_run_as_the_user(self):
        run = fake_run({})
        with unittest.mock.patch.object(rt.subprocess, "run", run):
            rt.main(["on", "midikeep"])
            rt.main(["off", "virtual-surround"])
        self.assertEqual(run.calls, [["ujust", "enable-midikeep"],
                                     ["ujust", "setup-virtual-surround", "disable"]])

    def test_terminal_switches_use_redfox_terminal(self):
        run = fake_run({"redfox-terminal prompt status": "on\n",
                        "redfox-terminal tools status": "off\n"})
        with unittest.mock.patch.object(rt.subprocess, "run", run):
            state = {t["id"]: t["on"] for t in rt.list_toggles()["toggles"]}
            rt.main(["on", "tools"])
            rt.main(["off", "prompt"])
        self.assertIs(state["prompt"], True)
        self.assertIs(state["tools"], False)
        self.assertEqual(run.calls[-2:], [["redfox-terminal", "tools", "on"],
                                          ["redfox-terminal", "prompt", "off"]])

    def test_dedup_states_its_memory_and_goes_through_the_helper(self):
        run = fake_run({f"{rt.DEDUP} status": "on\n",
                        f"{rt.DEDUP} plan --json": '{"uuid": "u", "memory_mb": 1536}\n'})
        with unittest.mock.patch.object(rt.subprocess, "run", run):
            toggles = {t["id"]: t for t in rt.list_toggles()["toggles"]}
            rt.main(["off", "dedup"])
        self.assertIs(toggles["dedup"]["on"], True)
        self.assertIn("uses 1.5 GB of memory", toggles["dedup"]["subtitle"])
        self.assertEqual(run.calls[-1], ["pkexec", rt.SYSTEM_HELPER, "dedup", "off"])

    def test_dedup_unavailable_reads_as_unknown(self):
        run = fake_run({f"{rt.DEDUP} status": "unavailable\n"})
        with unittest.mock.patch.object(rt.subprocess, "run", run):
            toggles = {t["id"]: t for t in rt.list_toggles()["toggles"]}
        self.assertIsNone(toggles["dedup"]["on"])
        self.assertIn("up to 2 GB", toggles["dedup"]["subtitle"])

    def test_unknown_id_is_refused(self):
        with self.assertRaises(SystemExit):
            with redirect_stdout(io.StringIO()), unittest.mock.patch("sys.stderr", io.StringIO()):
                rt.main(["on", "rm-rf"])


class TestHelper(unittest.TestCase):
    def test_every_system_toggle_is_allowed_by_the_helper(self):
        text = HELPER.read_text()
        for t in rt.TOGGLES:
            if t["system"]:
                self.assertRegex(text, rf"\n    {t['id']}\) (recipe=|exec )", t["id"])

    def test_helper_refuses_anything_else(self):
        for args in (["nope", "on"], ["tailscale", "maybe"], []):
            res = subprocess.run(["bash", str(HELPER), *args], capture_output=True, text=True)
            self.assertEqual(res.returncode, 2, args)

    def test_policy_points_at_the_helper(self):
        text = POLICY.read_text()
        self.assertIn('<action id="tech.redfoxlabs.hub.system-toggles">', text)
        self.assertIn("/usr/libexec/redfox-system-toggle</annotate>", text)


if __name__ == "__main__":
    unittest.main()

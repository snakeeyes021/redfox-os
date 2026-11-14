"""redfox-nord's machine-readable side for RedFox Hub: list --json, status --json, rules set and
token set. No network and no NetworkManager: those are faked.

    python3 -m unittest tests.test_redfox_nord_json
"""

import argparse
import importlib.machinery
import importlib.util
import io
import json
import shutil
import stat
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "files" / "system" / "usr" / "bin" / "redfox-nord"
loader = importlib.machinery.SourceFileLoader("redfox_nord", str(SCRIPT))
spec = importlib.util.spec_from_loader("redfox_nord", loader)
nord = importlib.util.module_from_spec(spec)
loader.exec_module(nord)

MANAGED = [
    {"uuid": "u1", "name": "NordVPN US #13024", "type": "wireguard", "server_num": "13024",
     "country_code": "US", "category": "standard", "active": True},
    {"uuid": "u2", "name": "NordVPN UK #2214", "type": "wireguard", "server_num": "2214",
     "country_code": "GB", "category": "standard", "active": False},
    {"uuid": "u3", "name": "NordVPN US #11250 (P2P)", "type": "wireguard", "server_num": "11250",
     "country_code": "US", "category": "p2p", "active": False},
]
COUNTRY_MAP = {"US": {"id": 228, "name": "United States", "code": "US"},
               "GB": {"id": 227, "name": "United Kingdom", "code": "GB"},
               "FR": {"id": 74, "name": "France", "code": "FR"}}
HEALTH = {228: {"13024": {"load": 12, "status": "online"}, "11250": {"load": 91, "status": "online"}},
          227: {}}


class NordJson(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.config = self.tmp / "redfox" / "config.yaml"
        patches = [
            unittest.mock.patch.object(nord, "USER_CONFIG_PATH", self.config),
            unittest.mock.patch.object(nord, "USER_CONFIG_DIR", self.config.parent),
            unittest.mock.patch.object(nord, "COUNTRY_CACHE", self.tmp / "cache" / "countries.json"),
            unittest.mock.patch.object(nord, "get_managed_connections", return_value=[dict(m) for m in MANAGED]),
            unittest.mock.patch.object(nord, "get_country_map", return_value=COUNTRY_MAP),
            unittest.mock.patch.object(nord, "get_country_server_health", side_effect=lambda cid: HEALTH[cid]),
            unittest.mock.patch.object(nord, "DEFAULT_CONFIG_PATH", self.tmp / "none.yaml"),
            unittest.mock.patch.object(nord, "REPO_DEFAULT_CONFIG", self.tmp / "none.yaml"),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def run_cmd(self, func, stdin="", **kwargs):
        out = io.StringIO()
        code = None
        with unittest.mock.patch.object(nord.sys, "stdin", io.StringIO(stdin)), redirect_stdout(out):
            try:
                func(argparse.Namespace(**kwargs))
            except SystemExit as e:
                code = e.code
        return out.getvalue(), code

    def test_list_json(self):
        out, code = self.run_cmd(nord.cmd_list_json, load=False)
        data = json.loads(out)
        self.assertIsNone(code)
        self.assertEqual(data["connected"], "u1")
        self.assertEqual([(s["number"], s["p2p"], s["active"]) for s in data["servers"]],
                         [("13024", False, True), ("2214", False, False), ("11250", True, False)])

    def test_list_json_with_load(self):
        out, _ = self.run_cmd(nord.cmd_list_json, load=True)
        servers = {s["number"]: s for s in json.loads(out)["servers"]}
        self.assertEqual((servers["13024"]["load"], servers["13024"]["online"]), (12, True))
        self.assertEqual(servers["11250"]["load"], 91)
        self.assertEqual(servers["13024"]["country_name"], "United States")
        # Missing from its country's list: gone.
        self.assertEqual((servers["2214"]["load"], servers["2214"]["online"]), (None, False))

    def test_list_json_offline_still_lists(self):
        with unittest.mock.patch.object(nord, "get_country_map", side_effect=ConnectionError("down")):
            out, code = self.run_cmd(nord.cmd_list_json, load=True)
        servers = json.loads(out)["servers"]
        self.assertIsNone(code)
        self.assertEqual(len(servers), 3)
        self.assertTrue(all(s["load"] is None for s in servers))

    def test_status_without_a_token(self):
        out, _ = self.run_cmd(nord.cmd_status, json=True, check=True)
        data = json.loads(out)
        self.assertEqual((data["provider_name"], data["token"], data["token_works"]), ("NordVPN", False, None))
        self.assertEqual(data["rules_from"], "default")
        self.assertEqual([r["country"] for r in data["rules"]], ["US", "UK", "FR", "DE", "JP"])
        self.assertIn({"code": "UK", "name": "United Kingdom"}, data["countries"])

    def test_status_checks_the_token(self):
        self.config.parent.mkdir(parents=True)
        self.config.write_text("nordvpn:\n  token: abc\n  servers:\n  - {country: FR, count: 2, category: p2p}\n")
        with unittest.mock.patch.object(nord, "token_works", return_value=False):
            out, _ = self.run_cmd(nord.cmd_status, json=True, check=True)
        data = json.loads(out)
        self.assertEqual((data["token"], data["token_works"], data["rules_from"]), (True, False, "config"))
        self.assertEqual(data["rules"], [{"country": "FR", "country_name": "France", "count": 2, "p2p": True}])

    def test_rules_set_keeps_the_rest_of_the_config(self):
        self.config.parent.mkdir(parents=True)
        self.config.write_text("nordvpn:\n  token: abc\nmachines:\n  x: {hostname: y}\n")
        out, code = self.run_cmd(nord.cmd_rules, action="set", stdin=json.dumps(
            [{"country": "United Kingdom", "count": 1, "p2p": False}, {"country": "us", "count": 2, "p2p": True}]))
        self.assertIsNone(code, out)
        cfg = nord.load_yaml(self.config)
        self.assertEqual(cfg["nordvpn"]["servers"], [{"country": "UK"},
                                                     {"country": "US", "count": 2, "category": "p2p"}])
        self.assertEqual(cfg["nordvpn"]["token"], "abc")
        self.assertEqual(cfg["machines"], {"x": {"hostname": "y"}})
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o600)

    def test_rules_set_refuses_bad_input(self):
        for bad in ("not json", json.dumps({"country": "US"}), json.dumps([{"country": "Narnia"}]),
                    json.dumps([{"country": "US", "count": 9}])):
            with self.subTest(bad=bad):
                _, code = self.run_cmd(nord.cmd_rules, action="set", stdin=bad)
                self.assertEqual(code, 1)
        self.assertFalse(self.config.exists())

    def test_token_set_checks_then_saves(self):
        with unittest.mock.patch.object(nord, "token_works", return_value=True) as works:
            out, code = self.run_cmd(nord.cmd_token, action="set", no_check=False, stdin="  tok-123\n")
        works.assert_called_once_with("tok-123")
        self.assertIsNone(code, out)
        self.assertEqual(nord.load_yaml(self.config)["nordvpn"]["token"], "tok-123")
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o600)

    def test_token_set_refused_or_unreachable_saves_nothing(self):
        for effect, expected in ((lambda t: False, 2), (ConnectionError("down"), 3)):
            with self.subTest(expected=expected), \
                    unittest.mock.patch.object(nord, "token_works", side_effect=effect):
                _, code = self.run_cmd(nord.cmd_token, action="set", no_check=False, stdin="tok")
                self.assertEqual(code, expected)
        self.assertFalse(self.config.exists())

    def test_token_works_reads_nords_refusals(self):
        # NordVPN answers a made-up token with 400 Bad Request; 401 and 403 also mean no.
        for error, expected in ((RuntimeError("NordVPN API error (400): Bad Request"), False),
                                (RuntimeError("NordVPN API error (403): Forbidden"), False),
                                (PermissionError("Unauthorized"), False)):
            with self.subTest(error=error), \
                    unittest.mock.patch.object(nord, "get_wireguard_private_key", side_effect=error):
                self.assertIs(nord.token_works("tok"), expected)
        with unittest.mock.patch.object(nord, "get_wireguard_private_key",
                                        side_effect=RuntimeError("NordVPN API error (502): Bad Gateway")), \
                self.assertRaises(ConnectionError):
            nord.token_works("tok")

    def test_status_never_fails_on_the_token_check(self):
        self.config.parent.mkdir(parents=True)
        self.config.write_text("nordvpn:\n  token: abc\n")
        with unittest.mock.patch.object(nord, "token_works", side_effect=RuntimeError("odd")):
            out, code = self.run_cmd(nord.cmd_status, json=True, check=True)
        self.assertIsNone(code)
        self.assertIsNone(json.loads(out)["token_works"])

    def test_token_set_needs_a_token(self):
        _, code = self.run_cmd(nord.cmd_token, action="set", no_check=True, stdin="  \n")
        self.assertEqual(code, 1)

    def test_country_names_use_the_cache_offline(self):
        nord.country_names(fetch=True)  # fills the cache
        with unittest.mock.patch.object(nord, "get_country_map", side_effect=ConnectionError("down")):
            self.assertEqual(nord.country_names(fetch=False).get("FR"), "France")


if __name__ == "__main__":
    unittest.main()

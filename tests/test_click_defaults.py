import ast
import importlib.machinery
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAYOUT = ROOT / "files" / "system" / "usr" / "bin" / "redfox-layout"
SETTINGS = ROOT / "files" / "hub" / "src" / "redfox_hub" / "settings.py"

# The click-action values each extension accepts (their gschema enums).
DOCK_VALUES = {"skip", "minimize", "launch", "cycle-windows", "minimize-or-overview", "previews",
               "minimize-or-previews", "focus-or-previews", "focus-or-appspread",
               "focus-minimize-or-previews", "focus-minimize-or-appspread", "quit"}
PANEL_VALUES = {"RAISE", "MINIMIZE", "LAUNCH", "CYCLE", "CYCLE-MIN", "QUIT", "TOGGLE-SHOWPREVIEW",
                "TOGGLE-CYCLE", "TOGGLE-SPREAD"}


def load_layout():
    try:
        import gi  # noqa: F401
    except ImportError:
        raise unittest.SkipTest("needs PyGObject")
    loader = importlib.machinery.SourceFileLoader("redfox_layout", str(LAYOUT))
    spec = importlib.util.spec_from_loader("redfox_layout", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def click_choices():
    tree = ast.parse(SETTINGS.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "CLICK_CHOICES":
            return ast.literal_eval(node.value)
    raise AssertionError("CLICK_CHOICES not found")


class TestClickDefaults(unittest.TestCase):
    def test_each_layout_starts_like_its_model(self):
        rl = load_layout()
        got = {name: (layout["settings"].get(rl.DTD, {}).get("click-action"),
                      layout["settings"].get(rl.DTP, {}).get("click-action"))
               for name, layout in rl.LAYOUTS.items()}
        self.assertEqual(got, {
            "redfox": ("focus-minimize-or-previews", None),
            "gnome": (None, None),
            "ubuntu": ("focus-or-appspread", None),
            "cal": ("skip", None),
            "wash": (None, "TOGGLE-SHOWPREVIEW"),
            "nostalgia": (None, "TOGGLE-SHOWPREVIEW"),
        })
        # Wash and Nostalgia show the current desktop's apps only; the dock
        # layouts leave it to GNOME's App Switching switch.
        for name, layout in rl.LAYOUTS.items():
            self.assertEqual(layout["settings"].get(rl.DTP, {}).get("isolate-workspaces"),
                             True if name in ("wash", "nostalgia") else None, name)
            self.assertNotIn("isolate-workspaces", layout["settings"].get(rl.DTD, {}), name)
        # Switching layout resets the taskbar's click too, not just the dock's.
        self.assertIn("click-action", rl.managed_keys()[rl.DTP])
        self.assertIn(rl.DTD, rl.RESET_SCHEMAS)

    def test_hub_choices_are_valid_and_cover_every_default(self):
        choices = click_choices()
        for name, text, panel, dock in choices:
            self.assertIn(panel, PANEL_VALUES, name)
            self.assertIn(dock, DOCK_VALUES, name)
            self.assertTrue(text, name)
        docks = {c[3] for c in choices}
        panels = {c[2] for c in choices}
        for value in ("focus-minimize-or-previews", "focus-or-appspread", "skip"):
            self.assertIn(value, docks)
        self.assertIn("TOGGLE-SHOWPREVIEW", panels)


if __name__ == "__main__":
    unittest.main()

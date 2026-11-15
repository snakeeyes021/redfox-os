"""Tiled windows following the tiling area (the layout extension's refit.js, run with gjs).
The expected places are where Tiling Shell itself put the same windows in the VM test.

    python3 -m unittest tests.test_refit
"""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFIT = ROOT / "files/system/usr/share/gnome-shell/extensions/redfox-layouts@redfoxlabs.tech/refit.js"

RUNNER = """
import {areaChanged, refitFrame, tiledFrame} from 'file://%s';
import System from 'system';
const cases = JSON.parse(ARGV[0]);
print(JSON.stringify({
    tiled: cases.tiled.map(([tile, area, gaps]) => tiledFrame(tile, area, gaps)),
    refit: cases.refit.map(([frame, tile, area, gaps]) => refitFrame(frame, tile, area, gaps)),
    changed: cases.changed.map(([a, b]) => areaChanged(a, b)),
}));
System.exit(0);
"""

# A 1280 x 800 screen with a 32 px top bar; the RedFox dock (87 px) on the left.
WITH_DOCK = {"x": 87, "y": 32, "width": 1193, "height": 768}
WITHOUT = {"x": 0, "y": 32, "width": 1280, "height": 768}
BOTTOM_LEFT = {"x": 0, "y": 0.5, "width": 0.5, "height": 0.5}
BOTTOM_RIGHT = {"x": 0.5, "y": 0.5, "width": 0.5, "height": 0.5}
WHOLE = {"x": 0, "y": 0, "width": 1, "height": 1}


def gaps(n):
    side = {"top": n, "right": n, "bottom": n, "left": n}
    return {"inner": side, "outer": side}


@unittest.skipUnless(shutil.which("gjs"), "gjs isn't here")
class Refit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cases = {
            "tiled": [
                [BOTTOM_LEFT, WITHOUT, gaps(8)],
                [BOTTOM_RIGHT, WITHOUT, gaps(8)],
                [BOTTOM_LEFT, WITH_DOCK, gaps(8)],
                [BOTTOM_RIGHT, WITH_DOCK, gaps(8)],
                [WHOLE, WITH_DOCK, gaps(20)],
                [BOTTOM_LEFT, WITHOUT, gaps(0)],
            ],
            "refit": [
                # Mutter pushed the window clear of the dock as it came back (x 87, width
                # unchanged): it goes into its tile beside the dock.
                [{"x": 87, "y": 420, "width": 628, "height": 372}, BOTTOM_LEFT, WITH_DOCK, gaps(8)],
                # Already in place.
                [{"x": 8, "y": 420, "width": 628, "height": 372}, BOTTOM_LEFT, WITHOUT, gaps(8)],
            ],
            "changed": [[WITH_DOCK, WITHOUT], [WITHOUT, dict(WITHOUT)], [None, WITHOUT]],
        }
        tmp = Path(tempfile.mkdtemp())
        try:
            runner = tmp / "run.js"
            runner.write_text(RUNNER % REFIT)
            res = subprocess.run(["gjs", "-m", str(runner), json.dumps(cases)],
                                 capture_output=True, text=True, timeout=60)
        finally:
            shutil.rmtree(tmp)
        if res.returncode != 0:
            raise AssertionError(res.stderr)
        cls.out = json.loads(res.stdout.strip().splitlines()[-1])

    def frame(self, x, y, width, height):
        return {"x": x, "y": y, "width": width, "height": height}

    def test_the_whole_width_without_the_dock(self):
        self.assertEqual(self.out["tiled"][0], self.frame(8, 420, 628, 372))
        self.assertEqual(self.out["tiled"][1], self.frame(644, 420, 628, 372))

    def test_beside_the_dock(self):
        self.assertEqual(self.out["tiled"][2], self.frame(95, 420, 585, 372))
        self.assertEqual(self.out["tiled"][3], self.frame(688, 420, 584, 372))

    def test_the_gap_setting_is_the_gap(self):
        self.assertEqual(self.out["tiled"][4], self.frame(107, 52, 1153, 728))
        self.assertEqual(self.out["tiled"][5], self.frame(0, 416, 640, 384))

    def test_a_window_pushed_aside_goes_back_into_its_tile(self):
        self.assertEqual(self.out["refit"][0], self.frame(95, 420, 585, 372))

    def test_one_in_place_stays(self):
        self.assertIsNone(self.out["refit"][1])

    def test_area_changes(self):
        self.assertEqual(self.out["changed"], [True, False, False])


if __name__ == "__main__":
    unittest.main()

"""Dewy's VLC keys (configure-vlc-dewy): the speed keys, and Left and Right jumping 5 seconds.

    python3 -m unittest tests.test_vlc_dewy
"""

import unittest

from tests.test_bootstrap import recipe_bodies


class VlcDewy(unittest.TestCase):
    def setUp(self):
        self.body = recipe_bodies()["configure-vlc-dewy"][1]

    def test_the_arrows_jump_five_seconds(self):
        # Plain Left/Right fall back to VLC's short jump when the video has no menus.
        self.assertIn('"core|short-jump-size=5"', self.body)

    def test_the_speed_keys_stay(self):
        for setting in ('"core|key-rate-slower-fine=s${tab}["', '"core|key-rate-faster-fine=d${tab}]"',
                        '"core|key-rate-normal=="', '"lua|lua-intf=redfox_speed"'):
            self.assertIn(setting, self.body)

    def test_dewys_profile_runs_it(self):
        self.assertIn("configure-vlc-dewy", recipe_bodies()["configure-dewy"][0])


if __name__ == "__main__":
    unittest.main()

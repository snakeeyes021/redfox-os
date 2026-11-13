"""RedFox Hub's command runner: finished lines, and progress redraws.

    python3 -m unittest tests.test_hub_host
"""

import sys
import unittest.mock
import unittest
from pathlib import Path

import gi

gi.require_version("GLib", "2.0")
from gi.repository import GLib  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "files/hub/src"))
from redfox_hub import host  # noqa: E402

SCRIPT = ("echo one; for i in 1 2 3; do printf '\\rprog %s' $i; sleep 0.3; done; "
          "printf '\\rdone line\\n'; printf 'win\\r\\n'; printf 'tail'; exit 3")


class TestRun(unittest.TestCase):
    def test_lines_and_progress(self):
        loop = GLib.MainLoop()
        events = []

        def done(rc, out):
            events.append(("done", rc, out))
            loop.quit()

        host.run(["bash", "-c", SCRIPT], on_done=done,
                 on_line=lambda line: events.append(("line", line)),
                 on_partial=lambda text: events.append(("partial", text)))
        GLib.timeout_add_seconds(10, loop.quit)
        loop.run()
        lines = [e[1] for e in events if e[0] == "line"]
        partials = [e[1] for e in events if e[0] == "partial"]
        self.assertEqual(lines, ["one", "done line", "win", "tail"])
        self.assertTrue(any(p and p.startswith("prog") for p in partials))
        self.assertIsNone(partials[-1])  # cleared before the finished line
        self.assertEqual(events[-1], ("done", 3, "one\ndone line\nwin\ntail"))

    def test_missing_command(self):
        loop = GLib.MainLoop()
        result = []
        host.run(["/nonexistent/command"],
                 on_done=lambda rc, out: (result.append((rc, out)), loop.quit()))
        GLib.timeout_add_seconds(5, loop.quit)
        loop.run()
        self.assertEqual(result[0][0], 127)

    def test_a_read_error_stops_the_command_and_reports(self):
        loop = GLib.MainLoop()
        result = []

        def done(rc, out):
            result.append((rc, out))
            loop.quit()

        # Decoding its first output fails, while the command would run for another minute
        broken = unittest.mock.Mock()
        broken.return_value.return_value.decode.side_effect = ValueError("boom")
        with unittest.mock.patch.object(host.codecs, "getincrementaldecoder", broken):
            host.run(["bash", "-c", "echo hi; sleep 60"], on_done=done)
            GLib.timeout_add_seconds(20, loop.quit)
            loop.run()
        self.assertEqual(len(result), 1)
        self.assertNotEqual(result[0][0], 0)
        self.assertIn("Stopped bash: boom", result[0][1])


if __name__ == "__main__":
    unittest.main()

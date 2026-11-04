"""Running RedFoxOS's command-line tools for the app.

Hub is a front end: everything it changes goes through a command that also
works in a terminal (redfox-updates, redfox-layout, redfox-software,
redfox-rollback-helper). Commands run in a worker thread; callbacks come back
on the GTK main loop.
"""

import json
import os
import subprocess
import threading

from gi.repository import GLib


def _env():
    env = dict(os.environ)
    env["LC_ALL"] = "C.UTF-8"
    env.pop("PYTHONPATH", None)
    return env


def run(argv, on_done=None, on_line=None):
    """Run argv in a thread.

    on_line(line) is called for each line of output (stdout and stderr
    together), on_done(returncode, output) once at the end. Both run on the
    main loop. Returns the thread.
    """

    def worker():
        lines = []
        try:
            proc = subprocess.Popen(
                argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, text=True, bufsize=1, env=_env())
        except OSError as error:
            message = f"Couldn't run {argv[0]}: {error.strerror}"
            if on_done:
                GLib.idle_add(on_done, 127, message)
            return
        for line in proc.stdout:
            line = line.rstrip("\n")
            lines.append(line)
            if on_line:
                GLib.idle_add(on_line, line)
        proc.wait()
        if on_done:
            GLib.idle_add(on_done, proc.returncode, "\n".join(lines))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread


def run_json(argv, on_done):
    """Run argv, parse its stdout as JSON and call on_done(data, error)."""

    def worker():
        try:
            proc = subprocess.run(
                argv, capture_output=True, text=True, stdin=subprocess.DEVNULL,
                env=_env(), timeout=120)
        except (OSError, subprocess.TimeoutExpired) as error:
            GLib.idle_add(on_done, None, str(error))
            return
        if proc.returncode != 0:
            message = (proc.stderr or proc.stdout).strip().splitlines()
            GLib.idle_add(on_done, None, message[-1] if message else
                          f"{argv[0]} failed ({proc.returncode})")
            return
        try:
            data = json.loads(proc.stdout)
        except ValueError as error:
            GLib.idle_add(on_done, None, f"{argv[0]}: bad output ({error})")
            return
        GLib.idle_add(on_done, data, None)

    threading.Thread(target=worker, daemon=True).start()


def run_events(argv, on_event, on_done=None):
    """Run a command that prints one JSON object per line (--json mode).

    Lines that aren't JSON are passed on as {"event": "log", "line": ...}.
    """

    def line(text):
        try:
            event = json.loads(text)
        except ValueError:
            event = {"event": "log", "line": text}
        if isinstance(event, dict):
            on_event(event)

    return run(argv, on_done=on_done, on_line=line)

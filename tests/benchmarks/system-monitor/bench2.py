#!/usr/bin/python3
"""Time to first useful data, and responsiveness, for the three system monitors.

For each start (cold: the app's and runtime's files dropped from the page
cache first; warm: straight after a previous start), on the hidden rfbench
display, through the accessibility tree:

  window   the app's window exists
  numbers  its first page shows at least 3 real readings (%, GHz, MB, °C...)
  list     after asking for the process list (a click on its tab/row),
           at least 10 rows with memory figures are on screen
  stall    the longest the app took to answer one accessibility call in
           the 10 s after its window appeared (its main loop being busy:
           clicks and scrolling would wait just as long)

    bench2.py RUNS_COLD RUNS_WARM
"""
import glob, json, os, re, subprocess, sys, time

import gi
gi.require_version("Atspi", "2.0")
from gi.repository import Atspi  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench import APPS, start, stop  # noqa: E402

NUM = re.compile(r"(?<![\w.])\d+([.,]\d+)?\s*(%|GHz|MHz|[kKMGT]i?B|[kKMG]?bit|B|°C|W|RPM)(/s)?(?!\w)")
MEM = re.compile(r"\d+([.,]\d+)?\s*([kKMG]i?B)\b")
ATSPI_NAMES = {"Mission Center": ("missioncenter", "mission center"),
               "Resources": ("resources",),
               "System Monitor": ("gnome-system-monitor", "system monitor")}
PROCESS_TARGET = {"Mission Center": ("page tab", "Apps"),
                  "Resources": ("list item", "Processes"),
                  "System Monitor": ("page tab", "Processes")}


def find_app(name):
    desk = Atspi.get_desktop(0)
    for i in range(desk.get_child_count()):
        a = desk.get_child_at_index(i)
        try:
            if a and a.get_name().lower() in ATSPI_NAMES[name] and a.get_child_count() > 0:
                return a
        except Exception:
            pass
    return None


def walk(root, budget=2500):
    """(texts, nodes) of the accessible tree, visiting at most `budget` nodes."""
    texts, nodes, todo = [], [], [root]
    while todo and len(nodes) < budget:
        x = todo.pop()
        try:
            nodes.append(x)
            n = x.get_name()
            if n:
                texts.append(n)
            for j in range(x.get_child_count() - 1, -1, -1):
                todo.append(x.get_child_at_index(j))
        except Exception:
            pass
    return texts, nodes


def ping(app):
    t = time.monotonic()
    try:
        frame = app.get_child_at_index(0)
        frame.get_child_count()
        frame.get_name()
    except Exception:
        pass
    return time.monotonic() - t


def open_process_list(name, app):
    role, label = PROCESS_TARGET[name]
    _, nodes = walk(app, 4000)
    for x in nodes:
        try:
            if x.get_role_name() == role and (x.get_name() == label or
                                              any(c.get_name() == label for c in walk(x, 12)[1])):
                parent = x.get_parent()
                si = parent.get_selection_iface() if parent else None
                if si and si.select_child(x.get_index_in_parent()):
                    return True
                ai = x.get_action_iface()
                if ai and ai.get_n_actions():
                    ai.do_action(0)
                    return True
        except Exception:
            pass
    return False


def drop_cache(name):
    paths = []
    app = APPS[name]
    if app["flatpak"]:
        paths += glob.glob(f"/var/lib/flatpak/app/{app['flatpak']}") + \
                 glob.glob(os.path.expanduser(f"~/.local/share/flatpak/app/{app['flatpak']}"))
        paths += glob.glob("/var/lib/flatpak/runtime/org.gnome.Platform/x86_64/50") + \
                 glob.glob(os.path.expanduser("~/.local/share/flatpak/runtime/org.gnome.Platform/x86_64/50"))
    else:
        info = json.loads(subprocess.run(["podman", "image", "inspect", "rfbench-gsm"],
                                         capture_output=True, text=True).stdout)[0]["GraphDriver"]["Data"]
        for key in ("UpperDir", "LowerDir"):
            paths += [p for p in info.get(key, "").split(":") if p]
    dropped = 0
    for root in paths:
        for dirpath, _, files in os.walk(root):
            for fn in files:
                p = os.path.join(dirpath, fn)
                try:
                    if os.path.islink(p) or not os.path.isfile(p):
                        continue
                    fd = os.open(p, os.O_RDONLY)
                    os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
                    os.close(fd)
                    dropped += 1
                except OSError:
                    pass
    return dropped


RESET_STATE = {
    # Resources reopens on the page it was left on; start each run on its default.
    "Resources": ["flatpak", "run", "--command=gsettings", "net.nokyan.Resources",
                  "reset", "net.nokyan.Resources", "last-viewed-page"],
}


def one_run(name):
    if name in RESET_STATE:
        subprocess.run(RESET_STATE[name], capture_output=True)
    t0 = time.monotonic()
    start(name)
    r = {"window": None, "numbers": None, "list": None, "stall": 0.0, "slow_pings": 0}
    app, asked = None, None
    while time.monotonic() - t0 < 40:
        now = time.monotonic() - t0
        if app is None:
            app = find_app(name)
            if app is not None:
                r["window"] = now
            else:
                time.sleep(0.05)
                continue
        p = ping(app)
        if r["window"] is not None and now - r["window"] <= 10:
            r["stall"] = max(r["stall"], p)
            r["slow_pings"] += p > 0.25
        texts, _ = walk(app)
        if r["numbers"] is None and sum(bool(NUM.search(t)) for t in texts) >= 3:
            r["numbers"] = time.monotonic() - t0
        if r["numbers"] is not None and asked is None:
            if open_process_list(name, app):
                asked = time.monotonic() - t0
        if asked is not None and r["list"] is None and sum(bool(MEM.search(t)) for t in texts) >= 10:
            r["list"] = time.monotonic() - t0
        if r["list"] is not None and now - (r["window"] or 0) > 10:
            break
        time.sleep(0.15)
    r["asked_list_at"] = asked
    stop(name)
    return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()}


def main():
    cold, warm = int(sys.argv[1]), int(sys.argv[2])
    Atspi.set_timeout(30000, 30000)
    results = {}
    for name in APPS:
        stop(name)
    only = sys.argv[3:]
    for name in APPS:
        if only and name not in only:
            continue
        runs = []
        for i in range(cold + warm):
            kind = "cold" if i < cold else "warm"
            time.sleep(3)
            if kind == "cold":
                drop_cache(name)
                time.sleep(1)
            res = one_run(name)
            res["kind"] = kind
            runs.append(res)
            print(name, json.dumps(res), flush=True)
        results[name] = runs
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bench2-" + "-".join(only or ["all"]).replace(" ", "_") + ".json"), "w") as f:
        json.dump(results, f, indent=1)


if __name__ == "__main__":
    main()

#!/usr/bin/python3
"""Compare system monitors on this machine, drawn on the hidden rfbench display.

    bench.py startup        3 cold-ish starts of each app, one at a time
    bench.py soak MINUTES   all three side by side, sampled every 30 s
    bench.py probe          dump each app's accessible text (GPU names etc.)
"""
import csv, json, os, subprocess, sys, time

TICK = os.sysconf("SC_CLK_TCK")
ENV = dict(os.environ, WAYLAND_DISPLAY="rfbench")
HERE = os.path.dirname(os.path.abspath(__file__))

APPS = {
    "Mission Center": {"start": ["flatpak", "run", "io.missioncenter.MissionCenter"],
                       "stop": ["flatpak", "kill", "io.missioncenter.MissionCenter"],
                       "flatpak": "io.missioncenter.MissionCenter", "comm": "missioncenter"},
    "Resources": {"start": ["flatpak", "run", "net.nokyan.Resources"],
                  "stop": ["flatpak", "kill", "net.nokyan.Resources"],
                  "flatpak": "net.nokyan.Resources", "comm": "resources"},
    "System Monitor": {"start": [os.path.join(HERE, "run-gsm.sh")],
                       "stop": ["podman", "stop", "-t", "2", "rfbench-gsm"],
                       "flatpak": None, "comm": "gnome-system-mo"},
}


def procs():
    out = {}
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            with open(f"/proc/{d}/stat") as f:
                s = f.read()
            comm = s[s.index("(") + 1:s.rindex(")")]
            rest = s[s.rindex(")") + 2:].split()
            with open(f"/proc/{d}/cmdline", "rb") as f:
                cmd = f.read().replace(b"\0", b" ").decode(errors="replace")
            out[int(d)] = {"ppid": int(rest[1]), "comm": comm, "cmd": cmd,
                           "cpu": int(rest[11]) + int(rest[12])}
        except (OSError, ValueError):
            pass
    return out


def descendants(table, roots):
    kids = {}
    for pid, p in table.items():
        kids.setdefault(p["ppid"], []).append(pid)
    seen, todo = set(), list(roots)
    while todo:
        pid = todo.pop()
        if pid in seen or pid not in table:
            continue
        seen.add(pid)
        todo.extend(kids.get(pid, []))
    return seen


def app_pids(name, table):
    app = APPS[name]
    roots = []
    if app["flatpak"]:
        ps = subprocess.run(["flatpak", "ps", "--columns=pid,application"], capture_output=True, text=True).stdout
        roots = [int(l.split()[0]) for l in ps.splitlines() if l.split()[1:2] == [app["flatpak"]]]
        # helpers started on the host with flatpak-spawn --host
        roots += [pid for pid, p in table.items() if f"/flatpak/app/{app['flatpak']}/" in p["cmd"]]
    else:
        roots = [pid for pid, p in table.items() if p["comm"] == app["comm"]]
    return descendants(table, roots)


def pss_kib(pids):
    total = 0
    for pid in pids:
        try:
            with open(f"/proc/{pid}/smaps_rollup") as f:
                for line in f:
                    if line.startswith("Pss:"):
                        total += int(line.split()[1])
        except OSError:
            pass
    return total


class CpuMeter:
    """CPU seconds used by an app, counting processes that have exited."""
    def __init__(self):
        self.last = {}
        self.gone = 0

    def update(self, table, pids):
        now = {pid: table[pid]["cpu"] for pid in pids if pid in table}
        for pid, cpu in self.last.items():
            if pid not in now:
                self.gone += cpu
        self.last = now
        return (self.gone + sum(now.values())) / TICK


def running(name):
    return any(APPS[name]["comm"] == p["comm"] for p in procs().values())


def stop(name):
    subprocess.run(APPS[name]["stop"], capture_output=True)
    for _ in range(50):
        if not running(name):
            return
        time.sleep(0.2)


def start(name):
    return subprocess.Popen(APPS[name]["start"], env=ENV, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=True)


def window_up(name):
    import gi
    gi.require_version("Atspi", "2.0")
    from gi.repository import Atspi
    desk = Atspi.get_desktop(0)
    want = {"Mission Center": ("missioncenter", "mission center"),
            "Resources": ("resources",),
            "System Monitor": ("gnome-system-monitor", "system monitor")}[name]
    for i in range(desk.get_child_count()):
        a = desk.get_child_at_index(i)
        try:
            if a and a.get_name().lower() in want and a.get_child_count() > 0:
                return True
        except Exception:
            pass
    return False


def startup(runs=3):
    results = {}
    for name in APPS:
        stop(name)
    for name in APPS:
        times = []
        for _ in range(runs):
            time.sleep(3)
            t0 = time.monotonic()
            start(name)
            meter, window_t, settled_t, history = CpuMeter(), None, None, []
            while time.monotonic() - t0 < 30:
                time.sleep(0.1)
                t = time.monotonic() - t0
                table = procs()
                history.append((t, meter.update(table, app_pids(name, table))))
                if window_t is None and window_up(name):
                    window_t = t
                # settled: window up and under 5% of a core over the last 0.5 s
                old = [h for h in history if h[0] <= t - 0.5]
                if window_t is not None and old and (history[-1][1] - old[-1][1]) / (t - old[-1][0]) < 0.05:
                    settled_t = t
                    break
            times.append({"window": window_t, "settled": settled_t})
            stop(name)
        results[name] = times
        print(name, json.dumps(times), flush=True)
    return results


def soak(minutes):
    for name in APPS:
        stop(name)
    for name in APPS:
        start(name)
        time.sleep(5)
    meters = {name: CpuMeter() for name in APPS}
    t0 = time.monotonic()
    path = os.path.join(HERE, "soak.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["minute", "app", "pss_mib", "cpu_s", "nprocs"])
        while True:
            t = (time.monotonic() - t0) / 60
            table = procs()
            for name in APPS:
                pids = app_pids(name, table)
                w.writerow([f"{t:.1f}", name, f"{pss_kib(pids) / 1024:.1f}",
                            f"{meters[name].update(table, pids):.2f}", len(pids)])
            f.flush()
            if t >= minutes:
                break
            time.sleep(30)
    print("soak done:", path)


def probe():
    import gi
    gi.require_version("Atspi", "2.0")
    from gi.repository import Atspi
    desk = Atspi.get_desktop(0)
    for i in range(desk.get_child_count()):
        a = desk.get_child_at_index(i)
        name = a.get_name() if a else ""
        if name.lower() not in ("missioncenter", "mission center", "resources", "gnome-system-monitor", "system monitor"):
            continue
        texts = []
        def walk(node, depth=0):
            if depth > 25 or len(texts) > 400:
                return
            try:
                n = node.get_name()
                if n:
                    texts.append(n)
                for j in range(node.get_child_count()):
                    walk(node.get_child_at_index(j), depth + 1)
            except Exception:
                pass
        walk(a)
        print(f"== {name}: {' | '.join(texts)[:3000]}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "startup":
        startup()
    elif cmd == "soak":
        soak(float(sys.argv[2]))
    elif cmd == "probe":
        probe()

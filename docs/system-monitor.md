# System monitor: Mission Center, Resources or GNOME System Monitor

Status: measured on Matt's laptop (i7-12700H, 20 threads, 64 GB, Intel Iris Xe + RTX 3080 Ti Mobile) on 2026-11-02. RedFox switches to **Resources** on `feat/system-monitor`.

## What was measured

Each app ran on a hidden virtual display (a headless mutter), so nothing appeared on Matt's screen. The versions were:
- Mission Center 1.2.0 and Resources 1.10.2, both from Flathub;
- GNOME System Monitor 50.0 from Fedora 44, run in a throwaway container because it isn't on Flathub. Its timings include about half a second of container start-up.

The measurements, all read through the accessibility tree:

- **Window:** the app's window exists.
- **Real numbers:** its first page shows at least three live readings (%, GHz, MB, °C…).
- **Process list:** after asking for it, at least ten rows with memory figures are on screen.
- **Longest stall:** the longest the app took to answer one accessibility call in its first 10 seconds. While the app's main loop is busy, clicks and scrolling wait just as long.
- **Memory:** proportional set size (PSS) of the app and its helper processes, sampled every 30 s over an hour, all three side by side.
- **CPU:** CPU time used, as a share of one core, over the hour and over a later 4.5-minute sample.

"Cold" means the app's and its runtime's files were dropped from the page cache first. "Warm" means it ran again straight after. Medians of 2 cold and 3 warm runs.

The machine was not idle: other work kept the load average between about 3 and 17. All three apps saw the same load, so the comparison is fair, but absolute CPU figures would be lower on a quiet machine.

## Results

| | Mission Center | Resources | GNOME System Monitor |
| --- | --- | --- | --- |
| Window appears (cold / warm) | 1.5 s / 1.3 s | 2.6 s / 2.6 s | 2.6 s / 2.7 s |
| **Real numbers on screen** (cold / warm) | **13.7 s / 13.1 s** (8–10 s in an earlier, less loaded round) | **3.2 s / 3.1 s** | **2.8 s / 2.9 s** |
| Process list on screen | ~17 s (it can only be opened once the numbers are in) | ~4 s | not measurable: its list isn't exposed to accessibility |
| Longest stall in the first 10 s | up to **8.3 s** (one cold run); otherwise ~0.7 s | 0.1 s | 0.1 s |
| Memory after 1 min → after 60 min | 301 → 308 MiB | 176 → 208 MiB (rising ~0.6 MiB/min) | 148 → 147 MiB |
| CPU, hour average (busy machine) | 33% of a core | 21% | 13% |
| CPU, later 4.5-min sample | 31% | 18% | 13% |
| NVIDIA GPU | yes | yes: load, video memory, clock, power, temperature, driver (checked on the RTX 3080 Ti) | no GPU view at all |
| Shows apps as well as processes, ends apps | yes | yes | processes only |
| Install | Flathub | Flathub | Fedora package; would have to be layered into the image |

What Matt saw is real. Mission Center puts its window up quickly, then shows an empty window for 8 to 14 seconds while its data gatherer starts. Once, it stopped answering altogether for over 8 seconds. Both other apps show real data within about a second of their window.

## Recommendation

**Resources.** It's the quickest to useful data apart from GNOME System Monitor, it's responsive from the start, it uses about two-thirds of Mission Center's memory and CPU, and it covers the NVIDIA card in full. It's also a GTK 4 / libadwaita app in GNOME Circle, and it's on Flathub.

GNOME System Monitor is the lightest, but it has no GPU view and isn't on Flathub, so RedFox would have to layer it into the image. That rules it out for a gaming and development machine.

Keep an eye on Resources' memory: it grew steadily over the hour (about 36 MiB), probably the history it keeps for each process's graph. If it keeps climbing over days, that's worth reporting upstream.

## Rerunning it

The scripts and raw results are in [`tests/benchmarks/system-monitor/`](../tests/benchmarks/system-monitor/):
- `bench.py` runs the hour-long side-by-side soak;
- `bench2.py` measures startup and responsiveness;
- `run-gsm.sh` and the `Containerfile` run GNOME System Monitor in a container.

They draw on a hidden display that must be started first:

    dbus-run-session -- mutter --headless --wayland --no-x11 --virtual-monitor 1920x1080 --wayland-display rfbench &
    python3 tests/benchmarks/system-monitor/bench2.py 2 3
    python3 tests/benchmarks/system-monitor/bench.py soak 60

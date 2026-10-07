# Midikeep: Continuous Background MIDI Recording Engine & Retrieval System

## Overview
**Midikeep** is an OS-level software counterpart to dedicated hardware MIDI loggers (such as Jamcorder). It runs silently in the background as an un-intrusive `systemd --user` service on RedFoxOS, capturing every Note-On, Note-Off, Pitch Bend, and Control Change (CC) event from all connected USB and virtual MIDI controllers.

### Core Philosophy
* **Zero Friction:** No DAW needs to be open, and no "Record" button ever needs to be pressed.
* **Never Lose an Idea:** Musical improvisation is ephemeral. Every chord progression, melody, or doodle played on any keyboard is automatically preserved.
* **Infinite Retention by Default:** MIDI data is exceptionally compact (an hour of vigorous playing rarely exceeds 100 KB). Storage retention defaults to **infinite**; past sessions are never pruned unless explicitly requested.
* **Blunt Silence Clustering (15-Minute Threshold):** Any playing constitutes a single contiguous session—even if it crosses a midnight boundary into the next day—unless there is a gap of **15 minutes or more** of silence. Natural pauses (adjusting patches, thinking over an arrangement, grabbing coffee) remain intact within the take.
* **Opt-In User Activation:** The daemon is baked into the immutable image but **disabled by default** to avoid consuming background resources for non-musician users. It is turned on via `ujust` recipes (`enable-midikeep`, `configure-music`, or `configure-matt`).
* **Instant DAW Ingestion:** Drag-and-drop or CLI-export recorded takes straight into Bitwig, Reaper, Ardour, Dorico, or file browsers.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   USB / HW MIDI Controller  |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   ALSA Sequencer (snd-seq)  |
                      +--------------+--------------+
                                     |
                [Auto-connects on device hotplug]
                                     |
                                     v
                      +-----------------------------+
                      |       midikeep-daemon       |
                      |   (systemd --user service)  |
                      |  [Opt-in via ujust recipes] |
                      +--------------+--------------+
                                     |
                      +--------------+--------------+
                      |                             |
                      v                             v
           +--------------------+         +-------------------+
           | Session Segmenter  |         | SQLite Index DB   |
           | (>15m Silence Split|         | (Metadata & Stats)|
           +----------+---------+         +-------------------+
                      |
                      v
           +--------------------+
           | Standard .mid Files|
           | (~/.local/share/   |
           |  midikeep/sessions)|
           +--------------------+
                      |
           +----------+----------+
           |                     |
           v                     v
+---------------------+ +----------------------+
|  midikeep CLI tool  | | midikeep-ui (GTK4)   |
| (Export, list, info)| | (Timeline, Piano-    |
|                     | |  roll, Drag & Drop)  |
+---------------------+ +----------------------+
```

---

## Epic 1: The Service & Storage Engine (`midikeep-daemon`)
*The headless background daemon and persistent event storage layer.*

### 1.1 Technical Stack & Dependencies
* **Core Language:** Python 3 (using `mido` with `python-rtmidi` or ALSA backend) or a compiled Rust/C binary leveraging `libasound2` (ALSA Sequencer API).
* **Base Dependencies:**
  * `alsa-lib` / `alsa-utils` (ALSA Sequencer client `snd-seq`).
  * `sqlite3` for query indexing.
  * Virtual MIDI loopback module (`snd-virmidi`) for automated testing.
* **Storage Location (XDG Compliant):**
  * Data Directory: `~/.local/share/midikeep/`
  * Sessions Directory: `~/.local/share/midikeep/sessions/YYYY/MM/DD/`
  * Index Database: `~/.local/share/midikeep/index.db`
  * Config Directory: `~/.config/midikeep/config.yaml`

### 1.2 Hotplug Device Detection & Port Subscription
* The daemon registers as an ALSA Sequencer client (`midikeep`).
* Subscribes to ALSA Sequencer system announcements (client/port creation and destruction events on port `0:1`).
* Automatically connects all readable MIDI input ports (hardware synthesizers, MIDI keyboards, electronic drum kits) to `midikeep`'s input port.
* Filters out clock tick jitter (`0xF8` MIDI Clock) and active sensing pulses (`0xFE`) unless MIDI beat clock logging is explicitly enabled in config.

### 1.3 Event Filtering & Take Clustering
* **Silence Threshold:** **15 minutes (900 seconds)** of inactivity.
* **Session Inception:** A new session begins immediately upon receiving the first Note-On event (velocity > 0).
* **Day & Midnight Continuity:** Sessions belong to the start date/timestamp. If a jam session starts at 11:30 PM and continues until 1:00 AM, it is preserved as a single continuous session file rather than being arbitrarily split at midnight.
* **Active State:** Captures Note-On, Note-Off, Velocity, Aftertouch, Poly-Pressure, Pitch Bend, and Control Changes (Sustain Pedal CC64, Modulation CC1, Expression CC11, etc.).
* **Session Finalization:** When no note events have arrived for `>= 15 minutes` (or on daemon shutdown):
  1. Any lingering held notes receive synthesized Note-Off messages.
  2. The Type 0 or Type 1 Standard MIDI file (`.mid`) is finalized with an End-of-Track meta event and written to disk:
     `~/.local/share/midikeep/sessions/YYYY/MM/DD/session_HH-MM-SS.mid`
  3. The SQLite database is updated with metadata for the session.
* **Crash Resilience:** During an active session, delta events are periodically flushed to temporary journal storage so unexpected system crashes or power cuts do not lose or corrupt unfinalized takes.

### 1.4 SQLite Index Schema (`index.db`)
```sql
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_seconds REAL NOT NULL,
    active_play_seconds REAL NOT NULL,
    note_count INTEGER NOT NULL,
    device_name TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    key_signature TEXT,
    tempo_bpm REAL DEFAULT 120.0,
    starred BOOLEAN DEFAULT 0,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_sessions_starred ON sessions(starred);
```

### 1.5 Systemd User Daemon Integration & Opt-In Policy
* **Unit File:** `/usr/lib/systemd/user/midikeep.service`
```ini
[Unit]
Description=Midikeep Background MIDI Recording Engine
After=sound.target pipewire.service
Wants=sound.target

[Service]
Type=simple
ExecStart=/usr/bin/midikeep-daemon
Restart=always
RestartSec=5s
Nice=-5
MemoryHigh=30M
MemoryMax=50M

[Install]
WantedBy=default.target
```
* **Activation Policy:**
  * **Not enabled by default globally** for all RedFoxOS users.
  * Packaged into the image at `/usr/lib/systemd/user/midikeep.service` and activated cleanly on a per-user basis.
  * Controlled via dedicated `ujust` recipes:
    * `ujust enable-midikeep`: Runs `systemctl --user enable --now midikeep.service`.
    * `ujust disable-midikeep`: Runs `systemctl --user disable --now midikeep.service`.
    * Included in `configure-music` (for any user setting up an audio workstation) and automatically chained into `configure-matt` / `bootstrap-matt`.

---

## Epic 2: Retrieval, CLI, and User Interface

### 2.1 The `midikeep` CLI Tool (`/usr/bin/midikeep`)
A companion command-line utility for status inspection, querying, live monitoring, and exporting.

* **Subcommands:**
  * `midikeep status`: Reports daemon status, active ALSA subscriptions, currently connected controllers, and total sessions recorded today.
  * `midikeep list [--today|--yesterday|--from <date>|--limit <N>]`: Tabular list of recorded sessions showing timestamp, duration, note count, device, and starred status.
  * `midikeep export [--last <duration>|--session <id>|--latest] -o <dest.mid>`:
    * Extracts an exact session or arbitrary time window (e.g. `midikeep export --last 10m -o idea.mid`).
  * `midikeep mark [-c COMMENT] [-i]`: Mark active take with a Clapper (★), embedding standard SMF marker meta-event `0xFF 0x06` and starring the take. If `-i` / `--interactive`, prompts via desktop dialog.
  * `midikeep comment [TEXT] [-i]`: Add a commented Clapper marker to active take.
  * `midikeep monitor`: Live terminal view printing incoming MIDI notes, velocities, and controllers in real-time (diagnostic mode).
  * `midikeep star <session_id>`: Flags a session as a favorite.
  * `midikeep prune --older-than <days>`: Optional manual cleanup (infinite retention remains default).

### 2.2 The Graphical Interface: Pianola (`tech.redfoxlabs.Pianola`)
A modern GTK4/Libadwaita desktop application adhering to GNOME Human Interface Guidelines (HIG).

* **Repository:** `snakeeyes021/pianola`
* **Distribution Model:** Standalone Flatpak bundle built via GitHub Actions and published via GitHub Releases (`tech.redfoxlabs.Pianola.flatpak`).
* **OS Integration:** Integrated into RedFox via `ujust install-pianola` and chained into `ujust install-audio` (and `install-creative` / `install-matt`).
* **Sandboxing & Permissions:**
  * `--filesystem=xdg-data/midikeep:rw` (Direct access to `~/.local/share/midikeep/index.db` and sessions/journal)
  * `--socket=pulseaudio`, `--socket=wayland`, `--socket=fallback-x11`
  * Bundled FluidSynth 2.4.1 and `FluidR3_GM.sf2` SoundFont for instant playback
  * File associations: `audio/midi;audio/x-midi;`
* **Key Views & Features:**
  1. **Visual Timeline & Day Picker:**
     * Infinite vertical/horizontal scrolling calendar.
     * Sessions rendered on a continuous strip, visual note density indicators.
  2. **Interactive Piano Roll Preview & Playback:**
     * Interactive vector piano roll with scrubbing, zooming, and playback via bundled FluidSynth.
  3. **Native Drag-and-Drop:**
     * Direct drag-and-drop export to DAWs (Bitwig, Reaper, Ardour) and file managers.
  4. **Tagging & Curation:**
     * Star button syncing with `index.db` starred status.

---

## Implementation Roadmap & File Placement

### Target Files in RedFoxOS Repository
| Path | Purpose |
|---|---|
| `files/system/usr/bin/midikeep-daemon` | Core headless ALSA listener & silence clustering daemon |
| `files/system/usr/bin/midikeep` | CLI control, export, and querying tool |
| `files/system/usr/lib/systemd/user/midikeep.service` | Systemd user service unit (opt-in) |
| `recipes/_common-modules.yml` | Base RPM dependencies (`alsa-utils`) |
| `files/system/usr/share/ublue-os/just/60-custom.just` | `enable-midikeep`, `disable-midikeep`, `install-pianola`, `install-audio`, `configure-music` recipes |

### Phase 1: Core Engine (Daemon + Storage) [COMPLETED]
1. Implement `midikeep-daemon` with ALSA Sequencer port autoconnect.
2. Implement 15-minute silence clustering logic and Type 0 MIDI writer.
3. Wire SQLite indexer (`index.db`) and crash journal (`journal/`).
4. Add user systemd unit and `enable-midikeep`/`disable-midikeep` ujust recipes.
5. Chain `enable-midikeep` into `configure-music` and `configure-matt`.

### Phase 2: CLI Interface & Export Engine [COMPLETED]
1. Implement `/usr/bin/midikeep` CLI with `status`, `list`, `star`, `export`, and `mark`.
2. Verified end-to-end extraction and SMF Type 0 validity.
3. Added `mark` (SIGUSR1 Clapper ★), `restart` (SIGUSR2), and commented clapper (`mark --comment` / `mark --interactive`).
4. Configured GNOME shortcuts:
   * `Ctrl+Alt+Super+K`: Instant Clapper take marker (★)
   * `Ctrl+Alt+Super+R`: Immediate take restart / finalize
   * `Ctrl+Alt+Super+M`: Commented Clapper take marker (interactive dialog)

### Phase 3: GTK4 / Libadwaita GUI: Pianola (`tech.redfoxlabs.Pianola`) [INTEGRATED]
1. Packaged as GNOME 47 Flatpak bundle with FluidSynth.
2. Added `ujust install-pianola` and `uninstall-pianola` to `60-custom.just`.
3. Chained `install-pianola` into `ujust install-audio`.

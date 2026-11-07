# RedFox Hub: design

Status: first version built on `feat/redfox-hub` (2026-11-04). The words, the illustrations and the looks are waiting for Matt.

RedFox Hub gives RedFox's own tooling (`redfox-*` scripts that used to be reached through `ujust` recipes) a GUI. It's for everyone who uses RedFoxOS, not only people at a terminal.

Each rule below is marked **(Matt)** if Matt decided it, or **(proposed)** if an agent proposed it and Matt hasn't confirmed it yet. Per AGENTS.md, only the (Matt) ones are settled.

## Decided by Matt

1. **One app, RedFox Hub** (`tech.redfoxlabs.Hub`). *(Matt, 11-02)*
2. **Five sections: Welcome, Apps, Updates, Settings, Manual.** *(Matt, 11-02; Updates added 11-04: "Redfox hub should also have the redfox updater incorporated". Updates being its own section, rather than part of Settings, was the PM's recommendation.)*
3. **First boot opens a GNOME Tour-style Welcome that ends in links.** The layout picker lives in Settings, not in Welcome. *(Matt)*
4. **Updates covers:** whether the automatic updates are on and when they last ran, a restart that's waiting, update now, the channel (stable `latest` or `unstable`), and rolling back with `redfox-rollback-helper`. RedFox runs its own updates with topgrade and uupd. "We are not Bazzite." *(Matt, 11-04)*
5. **No `ujust` in anything a user is shown.** Hub's switches are the long-term home for opt-in features. *(Matt, from the Winboat work)*
6. **Rebuild GNOME Tour's pattern in Python and libadwaita; don't fork its Rust code.** *(Matt, 11-03)*
7. **The name is written RedFoxOS, one word.** *(Matt)*
8. **Hub is built into the image, not a Flatpak:** "It is specific to the OS and wouldn't be helpful to others on a different OS." *(Matt, 11-04; this replaces his 11-02 "Flatpak in repo, remote later" for Hub.)* It's a meson project in `files/hub/`, installed to `/usr` at image build by `files/scripts/install-redfox-hub.sh`, as `tech.redfoxlabs.Hub`. Because it's part of the image, it's there at first boot (offline too, so Welcome needs no download step), it updates with the system, so it always matches the commands it calls, and it runs them directly, with no sandbox.

## Proposed (not yet confirmed)

- **Welcome shows once, after Bazzite Portal.** `/etc/xdg/autostart/tech.redfoxlabs.Hub.welcome.desktop` runs `/usr/libexec/redfox-hub-first-login`. That waits while Portal (`yafti_gtk`) is open, then runs `redfox-hub --first-login`, which shows the tour unless `~/.local/state/redfox/welcome-seen` exists. Existing users also see it once, after the update that brings Hub.
- **The pages and words of Welcome** (below).
- Everything under "Apps", "Settings" and the window layout below.

## The window

An `Adw.NavigationSplitView`: a sidebar (`Adw.Sidebar`) with Welcome, Apps, Updates, Settings and Manual, and the section on the right. On a narrow window the sidebar folds away, as in GNOME Settings. Every page can be opened directly:

```
redfox-hub --welcome              # the tour, in its own window
redfox-hub --page updates
redfox-hub --page settings/layout
redfox-hub --page manual/apps     # a Manual page, by its slug
```

The main menu has *Show the welcome tour* and *About RedFox Hub*.

## Principle: the GUI is a front end, the commands stay the source of truth

Every change Hub makes goes through a command that also works in a terminal. Each command prints JSON for Hub:

| Area | Command | JSON |
| --- | --- | --- |
| Updates | `redfox-updates status/now/auto on\|off/restart` | `status --json` |
| Channel, rollback, other builds | `redfox-rollback-helper rebase/rollback/list` | `--json list` |
| Layouts | `redfox-layout list/set` | `list --json` |
| Apps | `redfox-software list/install/remove` (catalog: `/usr/share/redfox/software.yaml`) | `--json` |
| Start at login | `redfox-autostart list/on/off` | `list --json` |
| MIDI archive | `midikeep data-dir [PATH]` | `data-dir --json` |

The `ujust` recipes (`install-*`, `configure-autostart-tray`, `preset-dock-*`, `rollback-helper`) call the same commands, so a terminal and Hub always do the same thing.

Passwords: nothing in Hub runs `sudo`. Changes that need root ask through polkit, in GNOME's own password dialog:
- rolling back needs no password for administrators, as in Bazzite's rpm-ostree rule;
- changing the channel or the build asks for one;
- turning automatic updates on or off asks for one, through `pkexec /usr/libexec/redfox-updates-auto` (polkit action `tech.redfoxlabs.hub.automatic-updates`).

## Stack

Python, GTK 4 and libadwaita 1.9, built with meson (`files/hub/`). Plain Python modules in `files/hub/src/redfox_hub/`, one per section; `style.css`, the layout previews, the Manual pages, the desktop entry and icons in `files/hub/data/`. Commands run in worker threads (`host.py`) and report back on the main loop.

## Welcome

GNOME Tour's pattern: full-window pages, each with one picture, a headline and a sentence or two. Arrows and dots move between them, and the last page links into Hub. It sets nothing up itself. At first login it opens in its own window; in Hub it's the Welcome section.

The words are a first draft for Matt *(proposed)*:

1. **Welcome to RedFoxOS.** The fox. "A fast, friendly desktop that looks after itself." *Take the Tour* / *Not Now*.
2. **Updates You Never Have to Think About.** "RedFoxOS updates itself in the background, all in one piece. If an update ever misbehaves, go back to the one before, in Hub or from the boot menu."
3. **Apps for Everything.** "Bazaar has thousands of apps from Flathub. RedFox's packs of favourites are in Hub, a tick away."
4. **Make It Yours.** Three layout previews. "Six layouts: a dock on the side or at the bottom, or one taskbar. Switch any time; your apps stay open."
5. **You're All Set.** *Get Apps*, *Choose a Layout*, *Read the Manual*, *Close*.

Pages 2, 3 and 5 use a large symbolic icon on a tinted disc as a stand-in. They're a good brief for the artist being commissioned for the fox.

## Updates

- **Status** at the top: updating (with a spinner), restart to finish, the last update didn't finish, automatic updates are off, or "Updates Are Automatic" with the time of the last update. **Update Now** runs `redfox-updates now` (topgrade with RedFox's config) and shows its output under *Details*. **Restart…** appears when a new system is waiting.
- **Automatic Updates:** a switch for `uupd.timer`, the last run (and whether it finished), the next run.
- **Channel:** Stable (`latest`) or Unstable, with a confirmation; a computer on a fixed build says so.
- **Go Back:** this system, the previous one with **Go Back…** (`rpm-ostree rollback`), and **Other Builds**, the recent builds of either channel from `redfox-rollback-helper --json list`, each with **Switch…**.

## Apps

The packs from the catalog, one group each, with each app's icon, name, a line of text and a tick for "installed". Tick or untick, then **Apply**; **Tick All** ticks a whole pack. Removing asks first. Each app shows a spinner while it's being installed. The personal bundles (Matt's, Dewy's) are hidden in Hub but stay as recipes.

## Settings

- **Layout:** the six layouts as cards, three across (two or one on a narrow window), in Matt's order, using the previews from `assets/layouts/`. Picking one applies it at once with `redfox-layout set`. Below the cards: the floating dock's gap, and the screen width from which the RedFox layout uses a dock.
- **Extra Dimming:** turns RedFox Dim on or off with `gnome-extensions enable|disable`. RedFoxOS's own shell extensions get a switch in Hub; features that aren't shell extensions stay plain OS files. The row only shows when the extension is installed.
- **Start at Login:** a switch per app (Signal, Joplin) to start it in the tray at login, through `redfox-autostart`. This is the roadmap's per-app tray toggle. `configure-matt` still runs `configure-autostart-tray` until Matt says the automatic step should go.
- **MIDI Archive:** where Midikeep keeps its recordings, with a folder chooser (`midikeep data-dir`). New takes go to the new folder; earlier ones stay where they were.
- Still to come *(proposed)*: desktop options (window buttons, app grid, tiling, corners, sounds), services (Tailscale, NordVPN, ClamAV, swap), this machine, setup profile, config file. Window buttons wait on one question: every layout sets them, so a separate switch would fight the layouts.

## Manual

A very short guide, only where RedFoxOS differs from ordinary Linux (it's immutable) or from other immutable systems (the tools RedFox chose). It's a searchable list of short pages, with commands in monospace boxes that have a copy button. The first set of pages (on `feat/hub-manual`):

- How RedFoxOS works: the image, what's yours, the three images.
- Updates and rolling back: automatic updates, restart to apply, the boot menu and Hub › Updates, `latest` versus `unstable`.
- Installing apps: Bazaar/Flathub first, then Homebrew for CLI tools, then distrobox, and layering with `rpm-ostree` only as a last resort.
- Shared dev environments ("my collaborators and I need identical setups with a specific Node version"): dev containers (VS Code + Docker/Podman) or distrobox.
- Python: uv, and pixi for conda-style projects, both preinstalled.
- Layouts: switching, and what each one is.
- Getting help: logs, and where to report a problem.

There's no page about `ujust`: it's no longer part of what users are shown, and no page mentions it.

### Files and format

The pages are part of Hub, in `files/hub/data/manual/` (installed to `<prefix>/share/redfox-hub/manual/`), and are reviewed like code. Hub reads them from there; the same files can be published on the RedFox website.

Each page is one file, `NN-slug.md`. `NN` (two digits) sets the order in the page list; the slug is the rest of the name, without `.md`, and is what links and `--page manual/<slug>` use.

Hub renders a strict subset of Markdown, so use only this:

- Line 1: `# Page title`. Then a blank line, then **one short sentence**: the page's summary, shown in the page list and in search.
- `## Section` headings. No `###` or deeper.
- Paragraphs, `-` bullet lists and `1.` numbered lists, one level only.
- `**bold**`, `` `inline code` `` and links: `[text](https://...)` for the web, `[text](manual:slug)` for another Manual page, and `[text](hub:updates)`, `[text](hub:settings/layout)` or `[text](hub:apps)` for a Hub page.
- Fenced code blocks marked ```` ```sh ````, holding commands the reader can copy: one command per line, with no prompt (`$`) and no output.

Nothing else: no tables, images, HTML, nested lists or blockquotes.

Keep to the differences: only where RedFoxOS differs from ordinary Linux or from other image-based systems. Each page should take under two minutes to read. Check every fact against the recipes and `files/`, and don't name a tool the image doesn't ship.

## Still to do

1. Matt's review of the looks and the Welcome words (previews on the tailnet).
2. The rest of Settings (above). Leave the config file page until the secrets/config design is settled.
3. Illustrations for Welcome, from the artist.

## Open questions for Matt

- Welcome's words and pages.
- Welcome and Bazzite Portal: keep "after Portal", or turn Portal off for RedFox users?
- Should existing users see the tour once after the update that brings Hub?
- `configure-autostart-tray` in `configure-matt`: drop it now that Hub has the switches?

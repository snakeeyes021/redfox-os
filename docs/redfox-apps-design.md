# RedFox Hub: design

Status: design. Matt has decided the shape (below); nothing is built yet. Building starts after Matt's review of the open branches.

This covers the "🧩 RedFox Apps (Flatpak GUIs)" section of the roadmap. The goal is to give RedFox's own tooling (today mostly `ujust` recipes and `redfox-*` scripts) a GUI, the way Thirties and Pianola are GUI apps.

## Decided

1. **One app: RedFox Hub** (`tech.redfoxlabs.Hub`), with four sections:
   - **Welcome**: a short, cheerful introduction to RedFoxOS. It opens by itself at first login.
   - **Apps**: RedFox's software packs, ticked and installed from a list.
   - **Settings**: layouts, desktop options, services and this machine.
   - **Manual**: short help pages on where RedFoxOS differs from other Linux systems.

   One app means one codebase, one Flatpak, one release and one set of permissions. The sections share the layer that runs commands on the host.
2. **A Flatpak, released the way Thirties and Pianola are.** Hub lives in its own repo and publishes a `.flatpak` bundle on its GitHub releases. This repo's `update-redfox-apps` lists it and installs and updates it per user, with an `install-redfox-hub` recipe. A RedFox Flatpak remote (a signed OSTree repo) can come later.
3. **Welcome runs after Bazzite Portal**, once Portal's window has closed, and leaves Portal on. This holds until Matt says otherwise.
4. **A first-login step fetches Hub.** Per-user bundles from GitHub need the network, and nothing installs them before the first login. So the image ships a small autostart entry: it runs `update-redfox-apps tech.redfoxlabs.Hub`, waits for Portal to close, then opens `tech.redfoxlabs.Hub --welcome`. A marker in `~/.local/state/redfox/` stops it after Welcome has been seen once. If the machine is offline, it tries again at the next login. A remote installed system-wide in the image would remove this step, which is one reason to revisit the remote later.

Hub changes the *host*: it runs `ujust`, `redfox-layout`, `flatpak install`, `rpm-ostree` and `gsettings` for the shell. It does that through `flatpak-spawn --host`, which needs `--talk-name=org.freedesktop.Flatpak`. That permission is effectively full access to the host, so the sandbox buys little. It also means Flathub wouldn't take Hub, but it isn't meant for Flathub.

## The window

An `Adw.NavigationSplitView`: a sidebar with **Welcome**, **Apps**, **Settings** and **Manual**, and the section on the right. On a narrow window the sidebar folds away, as in GNOME Settings. Each section can be opened directly, so Welcome, `ujust` messages and the Manual can link straight to a page:

```
flatpak run tech.redfoxlabs.Hub --welcome
flatpak run tech.redfoxlabs.Hub --page settings/layout
flatpak run tech.redfoxlabs.Hub --page manual/updates
```

There is one launcher in the app grid, **RedFox Hub**. It shouldn't share a name with GNOME's own *Settings* or *Software* apps, which "Hub" doesn't.

## Principle: the GUI is a front end, the CLIs stay the source of truth

Every action Hub takes goes through a host command that also works in a terminal, and that command can print JSON for the app:

| Area | Host command | Notes |
| --- | --- | --- |
| Layouts | `redfox-layout list/get/set` | Exists (on `feat/layout-modes`). Add `--json`. |
| Config | `redfox-config` | Exists. Its future shape depends on the secrets/config discussion. |
| Apps | `redfox-software list/install/remove` (new) | Reads a catalog file shipped in the image (below). |
| Recipes | `ujust <recipe>` | For anything not covered above. |

That keeps `ujust bootstrap-matt` and friends working unchanged and keeps the GUI thin. Hub checks the versions of the commands it calls, so an old image and a newer Hub fail clearly.

## Stack

The same stack as Thirties and Pianola: Python, GTK 4 and libadwaita, Meson, the `org.gnome.Platform` 50 runtime. It follows the GNOME HIG, and Blueprint can be used for UI files if it helps.

## Welcome

A brief, happy, clean introduction in the spirit of GNOME Tour: a few full-window pages, each with one big illustration, a one-line headline and a sentence or two. Arrows and dots move between pages. Then it hands over to the rest of Hub. It doesn't set anything up itself; that's what Apps and Settings are for.

Pages (a first draft of the words):

1. **Welcome to RedFoxOS.** The watercolour fox. "A fast, friendly desktop that looks after itself." Buttons: *Take the tour* and *Not now*.
2. **Updates you never have to think about.** RedFoxOS updates in the background as a whole system, and if an update ever misbehaves, you can go back to yesterday's with one choice at startup.
3. **Apps for everything.** Get apps from Bazaar (Flathub), with RedFox's packs of favourites a tick away.
4. **Make it yours.** The six layouts, drawn small (the previews from `assets/layouts/`), changing live.
5. **Made for making things.** Code, music and writing tools ready to go: VS Code, uv, containers, MIDI capture.
6. **You're all set.** Three large buttons into the rest of Hub: **Get apps** (Apps), **Choose a layout** (Settings › Layout) and **Read the Manual** (Manual). *Close* finishes Welcome.

### Reuse GNOME Tour?

[GNOME Tour](https://gitlab.gnome.org/GNOME/gnome-tour) is exactly this kind of app. It's licensed **GPL-3.0-or-later** and written in **Rust** (gtk4-rs and libadwaita), and it's small: a window, a paginator and an image-page widget.

- **Forking it** would give us its behaviour exactly. But Hub would then be Rust, unlike Thirties and Pianola, and Hub as a whole would have to be GPL-3.0.
- **Rebuilding the pattern** in Python is little work, because libadwaita now provides the pieces: `Adw.Carousel` with `Adw.CarouselIndicatorDots`, plus a page of picture, title and text. That's a few hundred lines, keeps one stack, and leaves the licence our choice.

**Recommendation: rebuild the pattern, and follow GNOME Tour's design closely**: its page layout, its pacing (about five pages), and its tone. If we copy any of its code or artwork, Hub becomes GPL-3.0, and that's fine too, but decide before starting.

The illustrations should be RedFox's own, in the watercolour style. They're a good brief for the artist being commissioned for the fox. Until then, the generated fox and the layout previews will do.

## Apps

A checklist of software grouped into the existing packs (Productivity, Daily, Creative, Music, Dev, Comms, Compatibility, …). Each row shows the app's icon, its name, one line of text, and whether it's installed. Ticking and pressing **Apply** installs or removes; a whole pack can be ticked at once.

For this to work, the software lists move out of the `install-*` recipes into a **catalog file in the image**, for example `/usr/share/redfox/software.yaml`:

```yaml
packs:
  productivity:
    name: Productivity
    items:
      - flatpak: org.libreoffice.LibreOffice
      - flatpak: com.getmailspring.Mailspring
  dev:
    name: Development
    items:
      - recipe: install-zed          # anything not a plain Flatpak stays a ujust recipe
      - brew: gh
```

`redfox-software` reads the file and the `install-*` recipes become one-liners (`redfox-software install productivity`), so the terminal and Hub always install the same things. Flatpak installs show per-app progress from `flatpak install --noninteractive`.

## Settings

Pages in the style of GNOME Settings:

- **Layout.** The layout picker: six cards, three across, in this order: **RedFox**, **GNOME** and **Ubuntu** on top, then **Cal**, **Wash** and **Nostalgia** ([`docs/layout-names.md`](layout-names.md); previews drawn by `assets/layouts/make-previews.py`, both on `feat/layout-modes`). Each picture has a very light border, so they line up by eye; a card lifts with a drop shadow on hover. `assets/layouts/picker.html` is a mock-up of the look. Picking one applies it live (`redfox-layout set`), so the user sees the real thing behind the window. Below the cards: the floating-dock gap, and the RedFox layout's "dock on screens at least N pixels wide".
- **Desktop.** Window buttons (`set-window-controls-*`), app grid sorting, tiling presets, square corners, sound theme, XWayland scaling. These are today's "UI/UX atoms", each a switch or a combo row that calls its recipe.
- **Services.** Tailscale, NordVPN, weekly ClamAV scans and swap, each with on/off and status.
- **This machine.** Hostname and hardware quirks, read from the `machines:` section of the config.
- **Setup profile.** Matt, Dewy or someone else (later "plain Fedora"). This picks the defaults that Apps pre-ticks, mirroring the `bootstrap-*` organisms without running them blind.
- **Config file.** View, import, export, or open `config.yaml` in an editor, with secrets masked. How secrets are stored and edited is the open secrets/config question, so this page waits for that.

## Manual

A very short guide, only where RedFoxOS differs from ordinary Linux (it's immutable) or from other immutable systems (the tools RedFox chose). It's a searchable list of short pages, with commands in monospace boxes that have a copy button. A first set of pages:

- How RedFoxOS works: the image, updates, rolling back, `unstable` versus stable.
- Installing apps: Bazaar/Flathub first, then Homebrew for CLI tools, then distrobox, and layering with `rpm-ostree` only as a last resort.
- "My collaborators and I need identical dev setups with a specific Node version": dev containers (VS Code + Podman/Docker) or distrobox.
- "I need a Python environment": uv (and pixi for conda-style projects), both preinstalled.
- `ujust`: what it is and the recipes worth knowing.
- Layouts: switching, and what each one is.
- Getting help: logs, and where to report a problem.

The pages are Markdown files in this repo (`docs/manual/`), so they can be reviewed like code. Hub bundles them at build time, and the same files can be published on the RedFox website.

## Suggested order

1. **Skeleton and Manual.** The window, the sidebar, deep links, the release pipeline and `update-redfox-apps`. The Manual is mostly writing and useful on its own.
2. **Settings › Layout.** The CLI exists and the previews are drawn.
3. **Apps.** The catalog refactor helps the `ujust` side too.
4. **Welcome and the first-login step.** Mostly illustration and words, and it links into the sections above.
5. **The rest of Settings.** Leave Config file until the secrets design is settled.

## Open questions for Matt

- Welcome's words and pages: the draft above, or a different story?
- GNOME Tour: rebuild its pattern in Python (recommended), or fork it (Rust, GPL-3.0)?
- Welcome and Bazzite Portal: keep "run after Portal", or turn Portal off for RedFox users?

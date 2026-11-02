# RedFox Apps: design proposal

Status: proposal for Matt to review. Nothing here is built yet.

This covers the "🧩 RedFox Apps (Flatpak GUIs)" section of the roadmap: **Welcome**, **Config**, **Software installer** and the **RedFox Manual**. The goal is to give RedFox's own tooling (today mostly `ujust` recipes and `redfox-*` scripts) a GUI, the way Thirties and Pianola are GUI apps.

## Decisions to make first

These shape everything below. My recommendation is first in each list.

1. **One app or four.** I recommend **one app, `tech.redfoxlabs.RedFox`, with four launchers**: *Welcome*, *RedFox Settings*, *RedFox Software*, *RedFox Manual*. The four overlap heavily. Welcome is a short tour through pieces of the other three, and Settings and Software both need the same "run this on the host" layer. One codebase means one Flatpak, one release and one place to fix things, and Flatpak allows extra launchers named `tech.redfoxlabs.RedFox.Manual.desktop` and so on. The alternative is four separate apps like Thirties and Pianola, which is cleaner per app but quadruples the packaging and release work for code that's mostly shared.
2. **Flatpak, or part of the image.** These apps change the *host*: they run `ujust`, `redfox-layout`, `flatpak install`, `rpm-ostree` and `gsettings` for the shell. A Flatpak can only do that through `flatpak-spawn --host`, which needs `--talk-name=org.freedesktop.Flatpak`. That permission is effectively full access to the host, so the sandbox buys little. The options:
   - **Flatpak with host access** (recommended, matches the roadmap). It updates on its own schedule, not the image's, and is built and released like Thirties and Pianola. Flathub wouldn't take it with that permission, but it isn't meant for Flathub.
   - **Part of the image** (Python + GTK in `/usr`, like `redfox-config`). There's no sandbox to work around, and it always matches the image's scripts. But every fix waits for an image build, and it can't be used on other distros (not a goal anyway).
3. **How it's installed.** Short term, use the existing `update-redfox-apps` fleet (GitHub release bundles, per user). Welcome must be there at first login, so in the longer term publish a small **RedFox Flatpak remote** (a signed OSTree repo on GitHub Pages or similar). The image would add it in `default-flatpaks` and install the app system-wide, and the Thirties and Pianola updates would come through it too.

## Principle: the GUI is a front end, the CLIs stay the source of truth

Every action the apps take goes through a host command that also works in a terminal, and that command can print JSON for the app:

| Area | Host command | Notes |
| --- | --- | --- |
| Layouts | `redfox-layout list/get/set` | Exists (on `feat/layout-modes`). Add `--json`. |
| Config | `redfox-config` | Exists. Its future shape depends on the secrets/config discussion. |
| Software | `redfox-software list/install/remove` (new) | Reads a catalog file shipped in the image (below). |
| Recipes | `ujust <recipe>` | For anything not covered above. |

That keeps `ujust bootstrap-matt` and friends working unchanged and keeps the GUI thin. The app checks the versions of the commands it calls, so an old image and a newer app fail clearly.

## Stack

The same stack as Thirties and Pianola: Python, GTK 4 and libadwaita, Meson, the `org.gnome.Platform` 50 runtime, and `tech.redfoxlabs.*` IDs. It follows the GNOME HIG, and Blueprint can be used for UI files if it helps.

## The four parts

### Welcome (first run)

Opens once per user at first login (an autostart entry that checks a marker in `~/.local/state/redfox/`). It can be reopened from the app grid. Steps:

1. **Hello.** One screen on what RedFox is, with a link to the Manual.
2. **Pick a layout.** Cards for GNOME, Ubuntu, macOS, Windows, Windows classic and RedFox, each with a screenshot. Picking one applies it live (`redfox-layout set`), so the user sees the real thing behind the window and can change their mind.
3. **Who's this for.** Matt, Dewy, or "someone else" (and later "plain Fedora"). This picks the defaults for the next steps, mirroring the `bootstrap-*` organisms without running them blind.
4. **Your config.** Import `config.yaml` (paste, file or URL, as `redfox-config setup` does) or skip. Depends on the secrets/config discussion.
5. **Software.** The Software page, pre-ticked for the profile chosen in step 3.
6. **Done.** It summarises what was applied (the bootstrap recap, as a list), offers to reboot if anything needs it, and links to the Manual.

Bazzite's own first-run app (Bazzite Portal) also starts at login. Welcome should turn that off for the user and link to it from the last page, rather than both opening.

### RedFox Settings (Config)

An `Adw.PreferencesWindow`-style app with these pages:

- **Layout.** The same cards as Welcome, plus the floating-dock gap and the RedFox layout's "dock on screens at least N pixels wide" setting.
- **Desktop.** Window buttons (`set-window-controls-*`), app grid sorting, tiling presets, square corners, sound theme, XWayland scaling. These are today's "UI/UX atoms", each a switch or a combo row that calls its recipe.
- **Services.** Tailscale, NordVPN, weekly ClamAV scans, swap: on/off and status.
- **This machine.** Hostname and hardware quirks, read from the `machines:` section of the config.
- **Config file.** View, import, export, or open `config.yaml` in an editor, with secrets masked. How secrets are stored and edited is the open secrets/config question, so this page waits for that.

### RedFox Software

A checklist of software grouped into the existing packs (Productivity, Daily, Creative, Music, Dev, Comms, Compatibility, …). Each row shows the app's icon, name and one line of text, and whether it's installed. Ticking and pressing **Apply** installs or removes; a whole pack can be ticked at once.

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

`redfox-software` reads the file and the `install-*` recipes become one-liners (`redfox-software install productivity`), so the terminal and the GUI always install the same things. Flatpak installs show per-app progress from `flatpak install --noninteractive`.

### RedFox Manual

A very short guide, only where RedFox differs from ordinary Linux (it's immutable) or from other immutable distros (the tools RedFox chose). It's a searchable list of short pages; commands sit in monospace boxes with a copy button. A first set of pages:

- How RedFox works: the image, updates, rolling back, `unstable` versus stable.
- Installing apps: Bazaar/Flathub first, then Homebrew for CLI tools, then distrobox, and layering with `rpm-ostree` only as a last resort.
- "My collaborators and I need identical dev setups with a specific Node version": dev containers (VS Code + Podman/Docker) or distrobox.
- "I need a Python environment": uv (and pixi for conda-style projects), both preinstalled.
- `ujust`: what it is and the recipes worth knowing.
- Layouts: switching, and what each one is.
- Getting help: logs, and where to report a problem.

The pages are Markdown files in this repo (`docs/manual/`), so they can be reviewed like code. The app bundles them at build time, and the same files can be published on the RedFox website.

## Suggested order

1. **Manual.** Mostly writing; useful on its own, and it shakes out the app skeleton and the release pipeline.
2. **Software.** The catalog refactor helps the `ujust` side too.
3. **Settings.** Start with the Layout page (the CLI exists), then Desktop and Services. Leave Config file until the secrets design is settled.
4. **Welcome.** Built mostly from the pages above.

## Open questions for Matt

- One app with four launchers, or four apps?
- Flatpak with host access, or part of the image?
- Is a RedFox Flatpak remote worth setting up now, or later?
- Should Welcome replace Bazzite Portal at first login, or run after it?
- App name: "RedFox" (with launchers named "RedFox Settings", "RedFox Software", and so on), or something else?

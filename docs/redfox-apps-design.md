# RedFox Apps: design

Status: design. Matt has decided the shape (below); nothing is built yet.

This covers the "🧩 RedFox Apps (Flatpak GUIs)" section of the roadmap: **Welcome**, **Config**, **Software installer** and the **RedFox Manual**. The goal is to give RedFox's own tooling (today mostly `ujust` recipes and `redfox-*` scripts) a GUI, the way Thirties and Pianola are GUI apps.

## Decided

1. **Two apps.** One app to *learn* RedFox and one to *change* it:
   - an **info app**: *Welcome* (first run) plus the *Manual*;
   - a **config app**: *Software* plus *Settings*.

   Each pair shares most of its code: Welcome is a tour that ends in the Manual, and Software and Settings both need the same "run this on the host" layer. Welcome's setup steps (layout, config, software) call the same host commands Workshop does, through a small shared library, so both apps need host access; the Manual on its own wouldn't.
2. **Flatpak, released the way Thirties and Pianola are.** Each app lives in its own repo and publishes a `.flatpak` bundle on its GitHub releases. This repo's `update-redfox-apps` lists the apps and installs and updates them per user, with an `install-*` recipe each. A RedFox Flatpak remote (a signed OSTree repo) can come later, when there are enough apps to justify it.

   Both apps change the *host*, the config app far more: it runs `ujust`, `redfox-layout`, `flatpak install`, `rpm-ostree` and `gsettings` for the shell. It does that through `flatpak-spawn --host`, which needs `--talk-name=org.freedesktop.Flatpak`. That permission is effectively full access to the host, so the sandbox buys little. It also means Flathub wouldn't take them, but they aren't meant for Flathub.

## Proposed names

| | Recommended | Alternatives |
| --- | --- | --- |
| Info app (Welcome + Manual) | **RedFox Guide**, `tech.redfoxlabs.Guide` | RedFox Field Guide; RedFox Den |
| Config app (Software + Settings) | *On hold* (working name "Workshop") | Matt felt "Workshop" sounds like you build things in it; the PM is offering him other names |

"Guide" says what it is: it greets you, then it's the manual. The config app's name is on hold; "Workshop" is used below only as a working name. Whatever it becomes, it shouldn't clash with GNOME's own *Settings* or *Software* apps in the app grid or search. Avoid "Toolbox" (Fedora's `toolbox` command) and "Tweaks" (GNOME Tweaks). Each app gets a second launcher for its other half, so the app grid shows *RedFox Guide*, *RedFox Manual*, *RedFox Workshop* and *RedFox Software*. Both launchers of an app open the same window on a different page.

## Still open

- **Welcome and Bazzite Portal.** Bazzite's own first-run app also starts at login. Working assumption: Welcome **runs after Portal** (once Portal's window has closed), and doesn't turn it off.
- **Welcome at first login.** Per-user bundles from GitHub need the network, and nothing installs them before the user first logs in. So the image needs a small first-login step: an autostart entry that runs `update-redfox-apps tech.redfoxlabs.Guide` and then opens Welcome. If it's offline, it tries again at the next login. A Flatpak remote installed system-wide in the image would remove this step, which is one reason to revisit the remote later.

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

## The info app (RedFox Guide)

### Welcome (first run)

Opens once per user at first login (the first-login step under "Still open", which checks a marker in `~/.local/state/redfox/`). It can be reopened from the app grid. Steps:

1. **Hello.** One screen on what RedFox is, with a link to the Manual.
2. **Pick a layout.** Cards for GNOME, Ubuntu, macOS, Windows, Windows classic and RedFox, each with a screenshot. Picking one applies it live (`redfox-layout set`), so the user sees the real thing behind the window and can change their mind.
3. **Who's this for.** Matt, Dewy, or "someone else" (and later "plain Fedora"). This picks the defaults for the next steps, mirroring the `bootstrap-*` organisms without running them blind.
4. **Your config.** Import `config.yaml` (paste, file or URL, as `redfox-config setup` does) or skip. Depends on the secrets/config discussion.
5. **Software.** Opens Workshop's Software page, pre-ticked for the profile chosen in step 3 (or offers to install Workshop first).
6. **Done.** It summarises what was applied (the bootstrap recap, as a list), offers to reboot if anything needs it, and links to the Manual.

Bazzite's own first-run app (Bazzite Portal) also starts at login. For now Welcome waits until Portal's window has closed and leaves Portal on (see "Still open").

### Manual

A very short guide, only where RedFox differs from ordinary Linux (it's immutable) or from other immutable distros (the tools RedFox chose). It's a searchable list of short pages; commands sit in monospace boxes with a copy button. A first set of pages:

- How RedFox works: the image, updates, rolling back, `unstable` versus stable.
- Installing apps: Bazaar/Flathub first, then Homebrew for CLI tools, then distrobox, and layering with `rpm-ostree` only as a last resort.
- "My collaborators and I need identical dev setups with a specific Node version": dev containers (VS Code + Podman/Docker) or distrobox.
- "I need a Python environment": uv (and pixi for conda-style projects), both preinstalled.
- `ujust`: what it is and the recipes worth knowing.
- Layouts: switching, and what each one is.
- Getting help: logs, and where to report a problem.

The pages are Markdown files in this repo (`docs/manual/`), so they can be reviewed like code. The app bundles them at build time, and the same files can be published on the RedFox website.

## The config app (name on hold; "Workshop" for now)

### Software

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

### Settings

An `Adw.PreferencesWindow`-style app with these pages:

- **Layout.** The same cards as Welcome, plus the floating-dock gap and the RedFox layout's "dock on screens at least N pixels wide" setting.
- **Desktop.** Window buttons (`set-window-controls-*`), app grid sorting, tiling presets, square corners, sound theme, XWayland scaling. These are today's "UI/UX atoms", each a switch or a combo row that calls its recipe.
- **Services.** Tailscale, NordVPN, weekly ClamAV scans, swap: on/off and status.
- **This machine.** Hostname and hardware quirks, read from the `machines:` section of the config.
- **Config file.** View, import, export, or open `config.yaml` in an editor, with secrets masked. How secrets are stored and edited is the open secrets/config question, so this page waits for that.

## Suggested order

1. **Guide: the Manual.** Mostly writing; useful on its own, and it shakes out the app skeleton and the release pipeline.
2. **Workshop: Software.** The catalog refactor helps the `ujust` side too.
3. **Workshop: Settings.** Start with the Layout page (the CLI exists), then Desktop and Services. Leave Config file until the secrets design is settled.
4. **Guide: Welcome.** Built mostly from the pages above, plus the first-login step.

## Open questions for Matt

- The info app's name: RedFox Guide, or one of the alternatives?
- The config app's name (on hold while Matt looks at alternatives to "Workshop").
- Welcome and Bazzite Portal: keep "run after Portal", or turn Portal off for RedFox users?

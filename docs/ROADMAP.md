# RedFoxOS Detailed To-Do

## 🚨 Infrastructure Fixes
- [x] **Migrate to DNF Module**
    - [x] Update `recipes/_common-modules.yml` to replace `rpm-ostree` module with `dnf`.
    - [x] Delete `containerfiles/dnf-overrides/Containerfile` once verified.
- [x] **Update README.md**
    - [x] Update "Rebasing" section: Explicitly warn about the Silverblue blocker (Signed Image vs. Unsigned Silverblue Policy).
- [ ] **Curate & Fix Flatpaks**
    - [x] **Fix "Nag on Boot":** Investigate and disable the repetitive Flatpak installation check on every boot.
    - [x] **Restore Missing Apps:**
        - [x] **Research:** Audit a fresh Silverblue rebase to identify *all* missing base apps (beyond just Firefox/Extension Manager).
        - [x] Ensure identified apps are in the default list.
    - [x] **Curate Defaults:** Review `recipes/_common-modules.yml` and remove unwanted placeholders.
        - [ ] **Research:** Can we inject the "Discrete GPU" preference file without forcing the app install? (if so, that should be a default; if not we may need to install Heroic by default)


## ⚙️ System Defaults (GSchema Overrides)
*These settings apply to everyone by default (via `gschema-overrides`).*

- [x] **Keyboard Shortcuts Strategy**
    - [x] Determine which shortcuts should be controlled by GNOME and which by Tiling Shell (the below might not all be correct)
        - [x] Navigation: `Ctrl`+`Super`+`Arrow` (Workspaces).
        - [x] Window Focus: `Super`+`Arrow` (the neighbouring window).
        - [x] Window Move (to a tile): `Super`+`Alt`+`Arrow`.
        - [x] Window Span: `Shift`+`Super`+`Arrow`.
        - [x] Close Window: `Super`+`q`.
- [x] **Dash to Dock (Disabled by default, but configured)**
    - [x] **Behavior:** Isolate Workspaces off (`false`); GNOME's App Switching setting "current workspace only" turns it on. *(Isolate Workspaces on (`true`) is Dewy's setting: `layout-dewy` turns on GNOME's App Switching "current workspace only", which the dock follows, so it survives layout switches.)*
    - [x] **Click Action:** `focus-minimize-or-previews` (Focus, minimize, or show previews).
    - [x] **Size:** Fixed icon size (Scroll to reveal).
    - [x] **Size:** Icon size limit (40px). *(40 px is layout-dewy's; the system default is 56 px)*
    - [x] **Appearance:** Shrink the dash (remove edge-to-edge).
- [ ] **App Grid Defaults**
    - [x] **Default:** alphabetical, with folders (Alphabetical App Grid, on by default).
    - [ ] **Folders off, and back on:** `flatten-app-folders` turns them off and `default-app-folders` brings back GNOME's default folders. *(Open question: how well a person's own folders can be restored after turning them off.)*
    - [ ] **GNOME's own order (not alphabetical), and back:** for vanilla-Fedora users and anyone who prefers it; `default-app-grid` exists. *(Open question: how well the original order comes back after switching to alphabetical and back.)*
    - [x] **Behavior:** Pinning to dock must not remove from grid. *(Default for everyone; the Fedora profile restores vanilla GNOME.)*
- [x] **Default dock apps:** Files, Firefox, Calculator, Text Editor, Bazaar and Settings, in that order (`org.gnome.shell favorite-apps`), then RedFox Hub, last, once Hub is in the image, in place of the set inherited from Bazzite. Only apps that are in the image or installed automatically at the first boot go in the default dock. Each layout keeps its own set.

## 📦 Default Software
- [x] **Dropbox:** Install official Dropbox client (flatpak)
    - [x] Remove maestral after dropbox is tested and experience is satisfactory (if maestral is not removed, improve maestral uninstall script to remove leftovers)
    - [x] **Starts at login:** the Flatpak's own "Start Dropbox on system startup" setting can't work from inside the Flatpak, so the image starts Dropbox at login for anyone who has it installed. Hub › Settings › Start at Login can turn it off.
- [x] **Implement** System-level GNOME Boxes + Virt-Manager
- [x] **Tailscale:** add to system defaults. *(Bazzite already ships Tailscale, off until `ujust tailscale enable`.)*
- [x] **No Winboat:** its install and uninstall recipes are gone, and so is FreeRDP, which was only there for it.
- [x] **Replace Mission Center** (slow to start, frozen at first, heavy on memory) with a better system monitor: Resources (`net.nokyan.Resources`) for new setups and the Dewy dock. Ctrl+Shift+Esc, Ctrl+Alt+Del on the keypad and Logo Menu's button open it through `redfox-system-monitor`, which falls back to Mission Center where that's all there is.
- [x] **VS Code:** install the Antigravity extension (`Google.google-antigravity`).
- [x] **No Antigravity app or Antigravity IDE in the image:** VS Code with the Antigravity extension takes the IDE's place. The Antigravity CLI (`agy`) is installed per user only on request, with `ujust install-antigravity-cli`; it isn't part of `install-dev`.
- [x] **T3 Code in the AI pack (AppImage + Gear Lever, stable or nightly):** a new AI pack (proposed; in Hub's Dev tab, `ujust install-ai`, and Matt's bundle) with T3 Code and Alpaca. T3 Code installs from its official AppImage, checked against its release's own checksums before anything runs, and Gear Lever (installed if missing) adds it to the app grid and keeps it updated on the chosen channel. The channel is a drop-down in Hub, and the terminal asks for it in `ujust install-ai`, `ujust install-t3code` and Full Setup.
- [ ] **Starship themes:** a picker with all of them (RedFox's own, Starship's default and its 12 official presets, plus off) in `redfox-terminal prompt theme`, Hub › Settings › Terminal and `ujust configure-terminal-prompt`; the fox as the OS symbol (style to be chosen: a small symbolic fox glyph); default after comparison. *(Built: the picker, with the presets shipped in the image; until the fox glyph is chosen they keep Starship's own OS symbols. Six use Nerd Font symbols: Catppuccin Powerline, Gruvbox Rainbow, Jetpack, Nerd Font Symbols, Pastel Powerline and Tokyo Night; RedFox ships the Symbols Nerd Font, so they show in any terminal font. Left: which fox glyph, and the default.)*
    - [x] **Terminal extras, opt-in:** `redfox-terminal` turns two things on or off for bash, zsh and fish: a styled prompt (Starship with RedFox's look, colours that read on light terminals too) and modern command-line tools (eza, ugrep, atuin, zoxide). RedFox Hub's Settings › Terminal has a switch for each.
    - [ ] **Open question: the default theme, and whether Starship is on by default.** Decided after comparing the three side by side in light and dark terminals. RedFox's own theme may be revised first, since its name makes it the natural default.

## 🌳 The `ujust` Architecture Tree
*The master plan for `files/system/usr/share/ublue-os/just/60-custom.just`.*

> **Architecture Note: Deviations vs. Resets**
> *   **Deviation Recipes** (e.g., `set-window-controls-right`) use `gsettings set` to apply specific user preferences.
> *   **Reset/Default Recipes** (e.g., `set-window-controls-left-gnome`) use `gsettings reset` to clear user overrides and revert to the system-wide baseline defined in `gschema-overrides`.

> **Architecture Note: Interactivity Strategy (The "Front Desk" Pattern)**
> *   **Goal:** To allow a user to run a long recipe (like `bootstrap-matt`) and immediately walk away without the script hanging 20 minutes later asking for a password or configuration link.
> *   **Implementation:** 
>     1. **`redfox-enforce-config` Atom:** The "Front Desk." It is the only place configuration is requested: if `~/.config/redfox/config.yaml` is missing it runs `redfox-config setup` (paste, file, or https URL). One config file describes all of a user's machines (NordVPN token and servers, plus a `machines:` section with per-machine hostname and hardware quirks).
>     2. **Dependency Chaining:** Any recipe chain that needs configuration lists `redfox-enforce-config` as its first dependency. `just` handles deduplication, so it only runs once per invocation.
>     3. **Silent Execution:** All other atoms read from `config.yaml` via `redfox-config` and skip gracefully when something isn't configured, recording what was skipped or failed in the end-of-bootstrap recap.
>     4. **Not yet met:** `sudo`/polkit prompts still happen inside individual recipes (hardware quirks, swap, hostname, ClamAV), though they cluster near the start of `configure-*`.

### Level 1: Atoms (Single-Purpose Scripts)
- [ ] `configure-git`: Interactive setup (User/Email/SSH) using `gh` CLI. *(A stub so far.)*
- [x] `setup-vscode`: *(Now the user-setup hook `90-vscode.sh`; the `configure-vscode` recipe is still a stub.)*
    - [x] **Task:** Compile final list of extensions.
    - [x] **Task:** Implement `jq` script to inject settings (Theme, Fonts, etc.).
- [x] `setup-cursor`: Mirror `setup-vscode` logic. *(Also in `90-vscode.sh`.)*
- [x] `install-zed`: Script to install Zed via `curl | sh` to `~/.local`.
- [x] `install-gemini-cli`: `brew install gemini-cli`. (deprecated/removed)
- [ ] `configure-heroic`: *(a stub so far)*
- [x] **UI/UX Atoms:**
    - [x] `fix-flatpak-theming`:
        - `sudo flatpak override --filesystem=xdg-data/themes`
        - `sudo flatpak mask org.gtk.Gtk3theme.adw-gtk3`
        - `sudo flatpak mask org.gtk.Gtk3theme.adw-gtk3-dark`
    - [x] `configure-tiling-dewy` (Deviation): *(now `layout-tiling-dewy`)*
        - [x] Show Indicator = true, Gaps (Inner/Outer) = 0.
        - [x] Enable Snap Assistant = false.
        - [x] **Keybindings:** Move (Super+Arrow), Cycle (Ctrl+Right Arrow), Focus (Remove Super+Arrow).
    - [x] `configure-tiling-default` (Reset): Revert Tiling Shell extension to system defaults. *(now `layout-tiling-default`)*
    - [x] `configure-text-editor-dev` (Deviation):
        - [x] Indentation: Spaces, 4 per tab/indent.
    - [x] `configure-text-editor-dewy-visuals` (Deviation): *(now `theme-text-editor-dewy`)*
        - [x] Dark Mode, Line Numbers, Overview Map, Highlight Current Line.
    - [x] `configure-text-editor-reset` (Reset): Revert indentation and visuals to system defaults.
    - [x] `set-window-controls-right-full` (Deviation): Sets `:minimize,maximize,close`.
    - [x] `set-window-controls-right-gnome` (Deviation): Sets `:close`.
    - [x] `set-window-controls-left-gnome` (Reset): Sets `close:` (reverts to system default).
    - [x] `sort-app-grid` (Hybrid): Keeps the app grid alphabetical (Alphabetical App Grid, on by default) and shows dock apps in it.
    - [x] `default-app-grid` (Deviation): GNOME's own order; new apps go at the end.
    - [x] `flatten-app-folders` (Deviation): Puts every app in the main grid, with no folders.
    - [x] `default-app-folders` (Reset): Restores the default app folders.
    - [x] `preset-dock-gnome` (Reset): Reset to default Gnome Dash (dash in overview)
    - [x] `_preset-dock-redfox` (Hybrid): TODO: A hacky stub of a recipe has been implemented; it works, but should be considered a proof of concept. *(Now `preset-dock-redfox`: the RedFox layout through `redfox-layout`. The layout helper extension switches between a floating dock on big screens and the GNOME dash on small ones, live, with no logout.)*
        - Default behavior will be to automatically switch between GNOME style dash and redfox style dock depending on monitor size (and scaling) -- this means we may need to create an additional recipe that sets the user to the default switching behavior and likely a systemd service to monitor monitor size(s)
        - The stub recipe requires logging out and logging in any time it is switched to or from
        - A true fix will likely involve forking (or getting a PR accepted with) Dash to Dock.
        - [x] Don't disable overview on startup (in dash to dock) -- it's a nice touch starting up to the overview
        - [x] Clock and Overview search should probably remain centered even if the usable workspace size changes
    - [x] `preset-dock-ubuntu` (Deviation): Configure Dash to Dock (Left side). Turn on Dash to Dock.
    - [x] `preset-dock-nostalgia` (Deviation): one taskbar along the bottom, start menu and apps on the left (Dash to Panel + ArcMenu).
    - [x] `preset-dock-wash` (Deviation): one taskbar along the bottom, start menu and apps centred (Dash to Panel + ArcMenu).
    - [x] `preset-dock-cal` (Deviation): a floating dock along the bottom (Dash to Dock).
    - [x] `configure-xway-scale-off` (Reset): Disable `xwayland-native-scaling` (reverts factor to default).
    - [x] `configure-xway-scale-on` (Deviation): Enable `xwayland-native-scaling` (forces factor to 0.0).
- [x] **Hardware Atoms (Must include Host Checks):**
    - [x] `fix-oryp9-mouse`: Udev rule (Run only if Oryp9).
    - [x] `fix-acer-nouveau`: Kernel args (Run only if Acer).

### Level 1.5: Small-ecules (Software packs)
- [x] `install-productivity`: Flatpak list (Office, etc.).
    - [x] potentially also `install-daily`: this and productivity may be one unit or two. This would include things like Tuba, RSS feed reader, Audiobook reader, etc.
- [x] `install-music`: Flatpak list (Ardour, Musescore, Lilypond, Frescobaldi, etc.).
- [x] `install-creative`: Flatpak list (Blender, Krita, Inkscape, Photo stuff, GIMP, Kdenlive, OBS etc.).
- [x] `install-dev`: Combines `install-zed`, `setup-vscode`, `setup-cursor`, `install-gemini-cli` (gemini cli deprecated/removed).
- [ ] **Torquio in RedFox Apps:** add it to the RedFox Apps pack once its Flatpak is published.

### Level 2: Molecules (Logical Groups)
- [ ] **Software Bundles (Install Molecules):**
    - [x] `install-matt`: Combines `install-dev`, `install-music`, `install-creative`, `install-productivity`, and `install-daily` if it is created.
    - [x] `install-dewy`
    - [x] `install-normie`: Combines `install-productivity`, `install-creative`, and `install-daily` if it is created.
    - [x] `install-fedora`: installs the apps Fedora Workstation ships, so `bootstrap-fedora` gets close to vanilla Fedora in one click. (The profiles let a RedFox user get close to vanilla Fedora, to Bluefin in a few clicks, or to a Bazzite-like look, as well as two developer setups.) *(Done as a "Fedora's Apps" pack in the software catalog, also in Hub: the apps in Fedora 45's Workstation package groups that RedFox doesn't already have. Calendar, Clocks, Contacts, Maps, Weather, Camera, Document Scanner, LibreOffice and Fedora Media Writer. GNOME Software is left out, since Bazaar is RedFox's store, and so is GNOME System Monitor, which isn't on Flathub (RedFox has Resources).)*
        - [x] A short proposal with two or three options and their trade-offs.

- [ ] **Config Molecules (User/Tool Setup):**
    - [ ] `configure-matt`:
        - [x] Runs Hardware Atoms (Logic checks happen inside atoms or here).
        - [x] Runs `configure-xway-scale-off`.
        - [ ] Runs `configure-git`.
        - [ ] Runs `configure-heroic` (if configure-heroic remains a ujust recipe and not a system default)
    - [ ] `configure-dewy`:
        - [x] Runs `configure-xway-scale-on`.
        - [x] **VLC speed keys** (`configure-vlc-dewy`; his preference, so his profile only, not a RedFox default): S and D step the playback speed down and up by 0.1, like the video speed controller he uses in the browser (VLC's fine speed keys, normally `[` and `]`). R toggles as the browser extension's does: at normal speed it goes to the last other speed used (1.8 to start with), otherwise back to normal. R is a small Lua interface VLC loads at every start (`redfox_speed.lua`). GNOME's video player is left out: its keys aren't settings.
        - [ ] **Task:** Determine configs and sub-recipes. *(Mostly done; left: the open Dewy items under Running Dewy fixes.)*
    - [x] `configure-fedora`:
        - [x] Runs `configure-xway-scale-on`.
        - [x] **Task:** Determine configs and sub-recipes: default keybindings, text editor reset, hostname, power saver, xwayland scaling.
    - [x] `configure-normie`:
        - [x] Runs `configure-xway-scale-off`.
        - [x] **Task:** Determine configs and sub-recipes: default keybindings, text editor reset, hostname, no suspend on AC, xwayland scaling off.

- [x] **Layout Molecules (UX/Behavior/Positioning):**
    - [x] `layout-matt` (Renamed from theme-matt):
        - [x] runs `sort-app-grid` and `flatten-app-folders`.
        - [x] runs `set-window-controls-left-gnome`.
    - [x] `layout-dewy` (Renamed from theme-dewy):
        - [x] Runs `sort-app-grid` and `flatten-app-folders`.
        - [x] Runs `set-window-controls-right-full`.
        - [x] Runs `preset-dock-ubuntu` (or custom Dewy dock settings).
    - [x] `layout-fedora`: "Reset" recipe to restore Vanilla Fedora layout.
    - [x] `layout-normie`: the flexible layout switcher is Hub's layout picker (done). The normie profile doesn't change the layout at all, keeping whatever the person has (RedFox's default unless they picked another). *(`bootstrap-normie` no longer runs `layout-normie`.)*

- [ ] **Theme Molecules (Visuals/Assets):**
    - [ ] `theme-matt`: Sets wallpapers, GTK theme (Adwaita Dark), Icons. *(Exists, for the text editor theme, sound and window corners; left: wallpapers, GTK theme, icons.)*
    - [ ] `theme-dewy`: Sets wallpapers, GTK theme (Adwaita Light), Icons. *(Exists, for the text editor theme and square corners; left: wallpapers, GTK theme, icons.)*
    - [x] `theme-fedora`: Reset visuals to default.

### Level 3: Organisms (User Bootstraps)
- [x] `bootstrap-matt`: Runs `install-matt`, `theme-matt`, `layout-matt`, `configure-matt`. *(Current order: `configure-matt`, `install-matt`, `theme-matt`, `layout-matt`, then a recap of what was done or skipped.)*
- [x] `bootstrap-dewy`: Runs `install-dewy`, `theme-dewy`, `layout-dewy`, `configure-dewy`. *(Current order: `configure-dewy`, `install-dewy`, `theme-dewy`, `layout-dewy`, then the recap.)*
- [x] `bootstrap-fedora`: Runs `theme-fedora`, `layout-fedora`, `configure-fedora` ~~(no install-fedora)~~. *(Current order: `install-fedora`, `theme-fedora`, `layout-fedora`, `configure-fedora`, then the recap.)*
- [x] `bootstrap-normie`: Runs `install-normie`, `theme-normie`, `layout-normie`, `configure-normie`. *(Then the recap. It no longer runs `layout-normie`: the normie profile leaves the layout alone.)*

## 🪟 Layout Modes
*`redfox-layout list/get/set` switches between the RedFox, GNOME, Ubuntu, Cal, Wash and Nostalgia layouts without logging out, and the `preset-dock-*` recipes call it. Wash and Nostalgia use Dash to Panel + ArcMenu.*
- [x] **Layout names that don't borrow other systems' names:** RedFox, GNOME and Ubuntu, then Cal, Wash and Nostalgia for the three modelled on other systems, with previews: [`docs/layout-names.md`](layout-names.md).
- [x] **More layouts, built from scratch:** all six (RedFox, GNOME, Ubuntu, Cal, Wash, Nostalgia) are written for RedFox in `redfox-layout`, and the `preset-dock-*` recipes call it.
- [x] **Switching layouts works live:** moving between layouts needs no logout or restart; the layout helper extension and smooth-overview follow the switch.
- [ ] **smooth-overview, hardened:** InjectionManager, safe to enable and disable twice, only the overview's and top bar's own lookups change, and the clock stays centred. Still to do: publish it on extensions.gnome.org.
- [x] **Maximize under a floating dock.** Whenever the dock is floating (it stops short of the screen edges, the same condition smooth-overview follows), a maximized window fills the whole screen except the top bar, covering the dock and its gaps, which is the same area as the smooth-overview work area. This applies to any setup with a floating dock, not particular layouts, and possibly to other docks such as Dash to Panel with margins. Tiled windows, including the full tile from dragging to the top, keep exactly the area and gaps they have today. Edge-to-edge docks and panels, and fullscreen, are unchanged. Possible route: while the dock floats, it stops reserving space and hides while a window is maximized, and Tiling Shell keeps being given the area beside the dock. *(Built that way, in Smooth Overview's "Maximized windows cover a floating dock" setting, which RedFox turns on. Dash to Panel isn't covered. New windows open beside the floating dock.)*
- [ ] **Wash and Nostalgia taskbars:** a taller panel with more room above and below the icons; Wash's start menu centred on the screen; an overview button next to the start button in place of the tiling button, since Super opens the start menu in these layouts; and the same panel content on every monitor (start button, overview button and tray icons). Tray icons only appear on the main panel today, so showing them on every monitor needs its own work. *(So far: the taller panel, Wash's start menu centred, an overview button next to the start button. Left: the tiling button is still there too, and tray icons only on the main panel.)*
- [x] **The taskbar follows "current workspace only":** Settings › Multitasking › App Switching › "Include apps from the current workspace only" now applies to the Nostalgia and Wash taskbar too, as it already did to the dock. While it's on, the taskbar shows only the current workspace's apps. While it's off, Dash to Panel's own switch is left as it is. *(Wash and Nostalgia now start with the taskbar showing the current desktop's apps only, as Windows' does; GNOME's switch turned off turns that off too. The other layouts show all workspaces.)*

## 💿 RedFoxOS ISO
*Today the only way to get RedFoxOS is to rebase onto it. The plan: a live ISO per image. See [`docs/iso.md`](iso.md).*

- [ ] **RedFoxOS ISO:** *(Shipped in 0.7. Left: the download page line below, and the proposed shrink.)*
    - [x] **Builder:** Universal Blue's Titanoboa, as Bazzite and Aurora use, for a live ISO with an installer. Replaces the old `build-iso.yml` (bootc-image-builder), which last ran on 2026-01-01 and failed.
    - [x] **Hosting:** the ISOs are over GitHub's 2 GiB limit for release files, so an object store such as Cloudflare R2. *(Cloudflare R2 behind download.redfoxlabs.tech.)*
    - [x] **Branding the installer:** RedFox's name, colours and fox in Anaconda.
    - [x] **Secure Boot and NVIDIA variants:** one ISO per image; the installer queues Universal Blue's key for enrolment.
    - [x] **Testing in a VM:** install each ISO on a blank disk with Secure Boot on, then check boot, login, updates and rollback.
    - [ ] **Before the download page goes live:** RedFox Hub, with its image picker for switching between the graphics images, is in the image. The page tells people they can switch to another image later from RedFox Hub. *(Hub is in the image; left: the page doesn't yet say you can switch images later in Hub.)*
    - [x] **Confirm the USB stick size for each ISO (8 GB vs 16 GB):** an 8 GB stick works with the NVIDIA Legacy ISO, the largest. The README and the download page don't name a size. Sizes:
        - RedFoxOS: 6.80 GB (6,802,345,984 bytes, 0.7)
        - RedFoxOS NVIDIA: 7.48 GB (7,478,710,272 bytes, 0.7)
        - RedFoxOS NVIDIA Legacy: 7.60 GB (7,604,654,080 bytes, 0.7); a 2026-11-07 test build was 7.94 GB
    - [ ] **Proposed: shrink the ISOs to leave headroom on 8 GB sticks.** The largest is close to 8 GB, and sticks sold as 8 GB vary in real size. Candidates, not yet measured:
        - The image to install is carried as a separate copy next to the live system. Installing from the live system's own files, or sharing their storage, could save the most.
        - Stronger compression for the live system's squashfs (higher-level zstd or xz), at the cost of build time and some boot speed.
        - Leave out of the live system what only the installed system needs, such as Flatpak runtimes or apps installed at build time, if there are any.
        - Drop locales, documentation and man pages from the live system only.
    - [x] **The graphics helpers reach main:** the page's commands run `extras/identify_gpu.sh` and `.ps1` from `main`, so the current helpers (they name the download to get, with no code to paste) reach people only once `unstable` is promoted. The page never points at `unstable`.

## 🧩 RedFox Hub
*One app for RedFox's own tooling, **RedFox Hub** (`tech.redfoxlabs.Hub`), with Welcome, Apps, Updates, Settings and Manual sections.*

- [ ] **Settings, the one place for RedFox's own settings:** Hub › Settings holds every setting RedFox adds on top of GNOME, grouped by what a person wants to change (taskbar, dock, overview, windows, dimming), never by extension name. Settings are added one at a time as people use them, not as a mirror of every extension option. GNOME's Settings app stays for GNOME's own settings, and Hub links to it where they meet; the Extensions app stays available for power users.
- [ ] A clean-up pass on Hub after real-world use testing.
- [ ] **Open question:** whether, how much and how to keep Bazzite's portal and settings: keep the Bazzite Portal in the image and adjust it there, integrate it into Hub, or fork GNOME Settings, as part of a broader settings discussion.
- [x] **Welcome:** a short, cheerful tour of RedFoxOS at first login, in the spirit of GNOME Tour, ending in links to Apps, Settings and the Manual.
    - [x] Apps still install at the first boot (they would make the ISOs too big), as the Welcome mentions.
    - [x] ~~Once they're in, maybe at the second login, a follow-up that helps arrange them.~~ *(Dropped: the app grid is alphabetical by default, so newly installed apps are easy to find.)*
- [ ] **Settings:** a front end to `redfox-config` / `config.yaml` and RedFox's settings, services and actions (see the setup-GUIs item in Fixups), including the layout picker with the RedFox layout names and previews. *(Done: the layout picker with names and previews, Start at Login, Terminal, Services, Storage, Sound & Music, Full Setup. Left: editing `config.yaml`.)*
    - [x] **"Start in tray at login" toggles, per app** (Signal, Joplin, and any others that support it). Long term there's no automatic autostart: each one is turned on in Hub, and the toggles write or remove the same autostart entries as `ujust configure-autostart-tray`. *(Signal, Joplin, Steam and Dropbox.)*
    - [x] **"MIDI archive folder" setting:** a folder chooser that writes `data_dir` to `~/.config/midikeep/config.yaml` and restarts the `midikeep` user service. Pianola should get the same in its preferences, since it reads the same file. *(Pianola's side: snakeeyes021/pianola#3.)*
- [x] **Apps:** a checklist of software and bundles (the `install-*` packs); tick and it installs them. *(Hub's Software page.)*
- [x] **Manual:** a very short help guide, only for where RedFoxOS differs from mainline Linux (it's immutable) or from other immutable distros (the conveniences and tools we chose). For example: "I want to install a Flatpak / a CLI tool, what do I do?", "My collaborators and I need identical dev setups with a specific Node version", "I need a Python environment; what are my options?" (uv, and whatever else we provide).

- [ ] **Graphical front ends in Hub for RedFox's CLI tools** (later): proper graphical controls for the command-line tools and ujust recipes RedFox ships (for example the Nord configurator), so nobody needs a terminal for them.
- [ ] **Full setup in one click:** a button in Hub, or at the end of the Welcome, that runs RedFox's full bootstrap for the person's setup (apps, layout, settings), with progress shown and a summary at the end of what was done or skipped.
    - [x] **Settings › Full Setup:** each profile (Matt, Dewy, Normie, Fedora) with its stages and steps, read from the `bootstrap-*` recipes, and a button that runs it in a terminal window (some steps ask for a password), ending with the recap. Every bootstrap step with a Hub switch uses the same tool as the switch, so Hub shows the result.
- [x] **Settings › Desktop › Clicking an Open App** (in unstable): what clicking an open app in the taskbar or dock does, set for both at once. Previews (one window shows or minimizes it, several show their previews), App Spread, Focus or App Spread, Bring Forward, Cycle, or Cycle, Then Minimize; "Other" when it's set in the dock's own settings. The row shows the current layout's dock, and is hidden in the GNOME layout, which has no dock.
    - [x] **Each layout's click behaviour follows the system it's modelled on** (switching layout resets it): RedFox, Previews; Ubuntu, Focus or App Spread, Ubuntu Dock's default ([ubuntu-dock schema override](https://git.launchpad.net/ubuntu/+source/gnome-shell-extension-ubuntu-dock/tree/schemas/10_ubuntu-dock.gschema.override)); Cal, Bring Forward, like the macOS Dock ([Apple](https://support.apple.com/guide/mac-help/use-the-dock-on-mac-mh35859/mac)); Wash and Nostalgia, Previews, like the Windows taskbar ([Microsoft](https://learn.microsoft.com/en-us/windows/win32/shell/taskbar-extensions)); GNOME, nothing to set.
- [x] **Steam doesn't start at login on new accounts:** a switch in Settings › Start at Login turns it on. Accounts that already have Bazzite's entry keep it, shown as on.
- [x] **New accounts start in the RedFox layout;** an existing account keeps its layout.
- [x] **The old RedFox Updater launcher goes:** Hub › Updates is the updater.
- [ ] **Open question, pinned:** replace Bazaar's Curated page (Bazzite's gaming-first list) with RedFox's own, built from the same packs as Hub's Software? Not decided; no work until it is.
- [ ] **Open question: rethink app packs vs Hub's app tabs.** Hub's Software page has a Packs tab alongside tabs (Dev, Gaming, Hardware) that are effectively more packs; how should packs and tabs relate?
- [ ] **Personal config export and import:** save a person's own setup to one file (profile picture, machine-specific tweaks, the VPN server fleet and similar) and use it during bootstrap on a new machine. Passwords and keys in the file are encrypted, and only settings that make sense on another machine are restored.

## 🖍️ Maniculos (screenshot markup)
*RedFox's own screenshot markup app, **Maniculos** (`tech.redfoxlabs.Maniculos`), in Python and libadwaita, in the Hub family. Capture stays with GNOME's screenshot tool, and Gradia (Flathub) covers markup until Maniculos ships.*

- [ ] **Maniculos: quick, easy markup for screenshots**, with exactly these features and nothing more:
    - [ ] Open from the clipboard, a file, or GNOME's "screenshot taken" notification (a "Mark up" button added by the layout helper extension)
    - [ ] Crop and rotate
    - [ ] Pen and highlighter, with colour and size
    - [ ] Arrow and rectangle
    - [ ] Text box
    - [ ] Blur or pixelate (to redact)
    - [ ] Undo and redo
    - [ ] Copy to clipboard (the main way out) and save

## 🧰 Editors
- [x] **Dewy and Sloppy extensions by default:** `RedFoxLabs.dewy` and `RedFoxLabs.sloppy` in VS Code and every fork we ship or set up (Cursor, Antigravity, etc.), from the VS Code Marketplace or Open VSX.

## 🧪 Testing
- [x] **VM testbed:** `tests/vm/` builds a Bazzite VM, `redfox-test`, and documents three ways to test a feature branch: a hotfix overlay, a local `bluebuild build` plus rebase, or CI's `pr-*` images.
- [ ] **Rebase from elsewhere now and then:** we normally rebase from Bazzite. Occasionally test rebasing from Bluefin (and other uBlue images) to make sure our setup holds up. Not pressing.
    - [x] Bluefin → RedFox: works; details in `tests/vm/README.md`. It takes about 45 minutes, since the images share no layers. Bluefin-only extensions (Search Light, Logo Menu) disappear without a message, and some packages drop a version until the next update.
- [x] **Bazzite recipes RedFox follows:** CI checks the Bazzite `ujust` recipes that RedFox has its own versions of (`tests/check_bazzite_recipes.py`), and fails when one changes. Bazzite's November changes are in: CoolerControl's container now has the system bus (its fan curves come back after suspend) and the time zone; RedFox's OpenRazer setup already matched. What RedFox does differently on purpose is noted per recipe in `tests/bazzite-recipes.json`.

## 🔐 User Config, Secrets & the ujust Audit
- [ ] **One secrets/config note per user:** the user keeps a single note in their secrets manager (Bitwarden or similar) that is their `~/.config/redfox/config.yaml`. It holds the settings that belong to the user rather than the OS, plus every secret or sensitive value, and RedFox sets everything else up from it automatically. Only a few integrations read it so far (NordVPN, per-machine hostname and quirks); audit which still need wiring.
- [ ] **API keys for agents and tools:** keys (Gemini, Anthropic, OpenAI, etc.) come from the config, and RedFox puts each where its tool expects it (keyring or environment) instead of hand-editing `.bashrc`. Agent sign-ins (Claude Code, agy, `gh`) stay a one-time prompt on first run unless an API key is configured.
- [ ] **Agent CLI themes:** terminal agents (Claude Code, agy, etc.) need a dark theme in the terminal but a light one inside VS Code. Claude Code's `auto` theme follows the terminal; agy has a `colorScheme` setting but no automatic mode yet. *(Done for Claude Code (its `auto` theme, by default); left: agy.)*
- [ ] **Audit the ujust recipes:** for each one, decide whether it belongs in the OS or is one user's quirk that should move into that user's config. Some stay on purpose, such as `bootstrap-matt` and `bootstrap-dewy`.

## 🛠️ Ujust Idempotency Fixes
- [x] **Research & Fix:** Identify and resolve recipes that fail or cause issues when run multiple times.
    - [x] `add-swap`: Idempotent; skips if already active at the requested size, recreates it if the size differs.
    - [x] `install-gemini-cli`: Fails if already installed via Homebrew. (No, this is fine as is--it's *supposed* to be installed via homebrew, and running this will update it) (gemini cli deprecated/removed)
    - [x] `uninstall-gemini-cli`: Fails if not installed. Now fixed. (deprecated/removed)
    - [x] `install-zed`: Should check for existing installation before running `curl | sh`. (No, this is not necessary; re-running will simply update it)
    - [x] `fix-oryp9-mouse`: Idempotent; checks if udev rule already exists and matches content.
    - [x] `configure-nordvpn`: Idempotent; `redfox-nord sync` only adds servers the profile is missing, so re-running changes nothing.

## 🎨 Branding & Aesthetics
- [ ] **Wallpapers**
    - [ ] Import all Bluefin / Bluefin DX wallpapers.
    - [ ] **Collection:** Collect more Paweł Czerwiński light/dark pairs (Unsplash License, credited). *(The default pair is his and credited in [`docs/wallpaper-credits.md`](wallpaper-credits.md), which also lists candidate pairs.)*
- [ ] **Maybe a GNOME/Adwaita theme for Firefox.** Bazzite's Fedora 44 base shipped update commands for one, dropped with its Topgrade include on Fedora 45. If we adopt it, it needs its own install and update path.
- [ ] **RedFoxOS Branding:** the OS calls itself RedFoxOS, not Bazzite, everywhere a person sees it. The trade-offs are in `docs/branding.md`.
    - [x] `os-release`: NAME/PRETTY_NAME "RedFoxOS", LOGO, URLs, DEFAULT_HOSTNAME `redfox`, BOOTLOADER_NAME, IMAGE_ID, and `ID=redfox` with `ID_LIKE="bazzite fedora"`.
    - [x] `image-info.json`: image name, vendor and ref are RedFox's (for the MOTD and Bazzite's scripts).
    - [x] Settings → About: name and logo (light and dark variants).
    - [x] GRUB entries: "RedFoxOS (ostree:N)".
    - [x] Login screen (GDM) logo: larger, light lettering for the dark background.
    - [x] Boot splash (Plymouth): RedFox watermark, larger and legible. It never showed before, because the initramfs kept Bazzite's copy; the build now rebuilds it.
    - [x] Fastfetch: RedFox fox in RedFox red, and the real booted image ref.
    - [x] Starship: a RedFox default config with a 🦊 OS symbol (Starship itself is the separate Starship item).
    - [x] Terminal banner (MOTD): RedFox welcome, links and tips; Bazzite's tips removed.
    - [x] Fedora logo files (installer, initial setup, About dialogs) regenerated from the RedFox art.
    - [x] Bazzite Portal is removed: RedFox Hub does its job (welcome, apps, updates, settings, fixes). Bazzite Announcements stay, without Bazzite's own messages.
    - [x] Bazzite's rollback helper (`bazzite-rollback-helper`, `bruh`) only knows Bazzite images. `redfox-rollback-helper` (`ujust rollback-helper`) lists builds of latest and unstable by commit and date, rolls back, and warns when a rebase switches NVIDIA flavour.
    - [x] Create/Add assets: Neofetch/Fastfetch Logo, Splash Screen, System Info Logo (made from the existing art by `assets/branding/make-images.py`).
    - [ ] **New artwork** (listed in `docs/branding.md`): the fox as an SVG; a simple single-colour fox mark for 16 px and symbolic icons (ArcMenu's start button, Logo Menu); the wordmark as a vector, or its font.
    - [ ] **Fox-face mark:** a simple, flat fox face for small sizes, used for the fastfetch logo (bigger than today's), ArcMenu's start button and the Logo Menu (white, symbolic), and 16–32 px icons.
    - [ ] **Commission a human artist** (e.g. on Fiverr) to paint the watercolour fox properly, and probably to redraw the face mark and the wordmark as vectors at the same time. Until then the current fox stays.

## Fixups/New (Items that arrive after a fix is already implemented)
- [x] Screenshot (add Windows super + shift + s shortcut for selection screenshot; move fullscreen screenshot to printscreen)
- [x] Check that Boxes is installing as system package and is cross-compatible with VMM
- [x] Change names for everything (Completed: Renamed to RedFoxOS)
- [x] Add sound theme change -- ujust (set default sound theme to normal fedora default, "reset". set sound to bazzite, "deviation")
    - [x] Set system default override to 'freedesktop' (Fedora default).
    - [x] Create ujust recipes: `theme-sound-fedora` (reset) and `theme-sound-bazzite` (set to 'bazzite').
- [x] Dock defaults
- [x] Set default hostname, etc (Implemented via static file `files/system/etc/hostname`) -- wrong, need to take a second swing at it (and remove the first attempt) -- Did we get this right? I think we did, but we should determine that and say so if so
- [ ] Cursor Remote Tunnels fixes from AmyOS
- [ ] vesktop icons fix (would like to use discord icons in system tray, perhaps different app icon too)
- [x] **Android Studio:** not in the default software; revisit if the /home → /var/home problem is fixed upstream.
- [ ] Bake Ollama
- [ ] implement 6 openclaw recipes (installs for openclaw, openclaw orchestrator, openclaw worker, and uninstalls for openclaw, orchestrator, and worker) -- see standalone to-do doc
- [ ] rounded blur issue in blur my shell
- [x] Joplin and Signal start minimized to the tray, but only when started at login; started any other way they open normally (`ujust configure-autostart-tray`).
- [x] Mailspring doesn't get Adwaita as its default theme, but it should. *(Shipped 2026-11-03: RedFox Adwaita Light and Dark, written from scratch, with Adwaita symbolic icons from the system theme and a small plugin for GNOME's button layout and Reply/Forward in the header; see [`docs/mailspring-adwaita.md`](mailspring-adwaita.md). Known limits: no GNOME split header, no native window corners or menus, and Mailspring puts the plugin's Reply group after its own buttons. A GNOME front end over Mailspring's sync engine was looked at and isn't recommended: [`docs/mailspring-gnome-frontend.md`](mailspring-gnome-frontend.md).)*
- [ ] Setup/bootstrapping/config GUIs for managing RedFox's app sets, settings, services, actions, etc. *(Hub now covers app sets, settings, services, actions and Full Setup; left: editing `config.yaml`.)*
- [ ] Midikeep: GNOME notifications don't group.
- [x] Midikeep: let the user set where the session archive goes, in a config Pianola also reads: `data_dir` in `~/.config/midikeep/config.yaml` (see `docs/midikeep.md`); Pianola side in snakeeyes021/pianola#3.


## Running Matt fixes
- [ ] Post-GNOME Builder install fix to reset file associations (GNOME builder steals just about any type of code file, python, json, sh, etc.)
- [x] Text Editor should not open previous session by default
- Manual steps still to automate:
    - [x] Install T3 *(Matt's bundle includes the AI pack.)*
    - [ ] Install Claude Code
    - [ ] GitHub CLI (`configure-git` uses `gh`; make sure it's installed)
    - [ ] Insync folders as Nautilus bookmarks (named with both the local user and the Google account email); maybe also symlinked into Wine prefixes and/or home
    - [ ] Profile picture

## Running Dewy fixes
- [x] System Dropbox
- [x] Cursor ruff extension (in ujust)
    - cursor --install-extension charliermarsh.ruff --force
- [x] cursor dark modern theme
- [x] texlive auto select version (latest)
- [x] tray defaults (files, mission center, settings, terminal, firefox, brave, calculator, text editor, zed, cursor, spotify, slack, signal, vesktop
- [x] brave in install-dewy
- [x] slack in install-dewy
- [x] square window corners (in as many situations as possible--libadwaita, gtk3, flatpak, etc.)
- [x] cli speedtest (speedtest.net cli--system install)
- [x] reverse screenshot shortcuts
- [ ] dewy: nightlight off
- [ ] dewy: accent color: teal
- [ ] dewy: when plugged in: automatic screen blank and automatic suspend off (on battery: 15 minutes)
- [ ] dewy: tilix settings:
    - follow instructions at: https://gnunn1.github.io/tilix-web/manual/vteconfig/ preferences->profiles->Default->Command-> click "Run command as login shell" (NOTE: this step has already been attempted and there are still outstanding issues. The instructions are subsequently known to be either incomplete, insufficient, or incorrect for this project and more investigation is needed--specifically, while we do ensure that vte.sh is sourced from /etc/profile.d, where it definitely already exists and is probably already being sourced anyways, we're still getting the warning on tilix on each startup... maybe tilix always shows that? probably not; it seems to say that a configuration issue is DETECTED--it seems to work when using fish as our shell, so at least our solution there seems to either be working or superfluous)
    - General Tab -> custom font size = 16
    - goto Color Tab
    -> set color scheme "Orchis"
    -> set background color to dark grey (e.g. #161616) (black too hard to see on black backgrounds)
    -> set transparency to 25% and unfocused dim to 50%
    - additional tilix issues: getting tilix set as the nautilus context menu "Open in terminal" is not working yet either. There is a nautilus extension for this called "nautilus-open-any-terminal" but we have yet to get this working also.
- [ ] GDM has monitors switched. Suspect we can simply have a ujust that takes user settings and applies them globally to whatever's in /etc/
- [ ] get vpn settings file
- [ ] dewy: qbittorent in flatpak recipe
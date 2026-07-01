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
        - [x] Window Move: `Shift`+`Super`+`Arrow`.
        - [x] Tiling Snap: `Super`+`Arrow`.
        - [x] Close Window: `Super`+`q`.
- [x] **Dash to Dock (Disabled by default, but configured)**
    - [x] **Behavior:** Isolate Workspaces (`true`).
    - [x] **Click Action:** `minimize-or-previews` (Focus, minimize, or show previews).
    - [x] **Size:** Fixed icon size (Scroll to reveal).
    - [x] **Size:** Icon size limit (40px).
    - [x] **Appearance:** Shrink the dash (remove edge-to-edge).
- [ ] **App Grid Defaults**
    - [ ] **Behavior:** Sort alphabetically (no folders).
        - [ ] Add behavior to keep user's folders saved, so they can go back to them if they want
    - [ ] **Behavior:** Pinning to dock must not remove from grid.

## 📦 Default Software
- [x] **Winboat:** Determine installation (DNF/Flatpak) and add to system defaults.
- [x] **Dropbox:** Install official Dropbox client (flatpak)
    - [x] Remove maestral after dropbox is tested and experience is satisfactory (if maestral is not removed, improve maestral uninstall script to remove leftovers)
- [x] **Implement** System-level GNOME Boxes + Virt-Manager
- [ ] **Implement** Starship terminal prompt by default with light-theme terminal (steal from Bluefin)
    - [ ] **Implement** ujust "configure" recipes for starship bluefin (system default, "reset"), starship bazzite (deviation), starship off (deviation)

## 🌳 The `ujust` Architecture Tree
*The master plan for `files/system/usr/share/ublue-os/just/99-redfox.just`.*

> **Architecture Note: Deviations vs. Resets**
> *   **Deviation Recipes** (e.g., `set-window-controls-right`) use `gsettings set` to apply specific user preferences.
> *   **Reset/Default Recipes** (e.g., `set-window-controls-left-gnome`) use `gsettings reset` to clear user overrides and revert to the system-wide baseline defined in `gschema-overrides`.

> **Architecture Note: Interactivity Strategy (The "Front Desk" Pattern)**
> *   **Goal:** To allow a user to run a long recipe (like `bootstrap-matt`) and immediately walk away without the script hanging 20 minutes later asking for a password or configuration link.
> *   **Implementation:** 
>     1. **`setup-secrets` Atom:** A dedicated atom acts as the "Front Desk." It is the *only* place interactivity (prompts for URLs, VPN credentials, etc.) is allowed. It caches these answers securely in `~/.config/redfox/secrets.env`.
>     2. **Dependency Chaining:** Any recipe (Level 1, 2, or 3) that requires a secret or `sudo` MUST list `setup-secrets` as its very first dependency. `just` handles deduplication, meaning `setup-secrets` will only run once per `just` invocation, even if 10 sub-recipes depend on it.
>     3. **Sudo Caching:** `setup-secrets` runs `sudo -v` immediately to cache the root password.
>     4. **Silent Execution:** All other scripts/atoms must be completely non-interactive. They read from the cached `secrets.env` file or fail gracefully if it is missing.

### Level 1: Atoms (Single-Purpose Scripts)
- [ ] `configure-git`: Interactive setup (User/Email/SSH) using `gh` CLI.
- [x] `setup-vscode`:
    - [x] **Task:** Compile final list of extensions.
    - [x] **Task:** Implement `jq` script to inject settings (Theme, Fonts, etc.).
- [x] `setup-cursor`: Mirror `setup-vscode` logic.
- [x] `install-zed`: Script to install Zed via `curl | sh` to `~/.local`.
- [x] `install-gemini-cli`: `brew install gemini-cli`. (deprecated/removed)
- [ ] `configure-heroic`:
- [ ] **UI/UX Atoms:**
    - [x] `fix-flatpak-theming`:
        - `sudo flatpak override --filesystem=xdg-data/themes`
        - `sudo flatpak mask org.gtk.Gtk3theme.adw-gtk3`
        - `sudo flatpak mask org.gtk.Gtk3theme.adw-gtk3-dark`
    - [x] `configure-tiling-dewy` (Deviation):
        - [x] Show Indicator = true, Gaps (Inner/Outer) = 0.
        - [x] Enable Snap Assistant = false.
        - [x] **Keybindings:** Move (Super+Arrow), Cycle (Ctrl+Right Arrow), Focus (Remove Super+Arrow).
    - [x] `configure-tiling-default` (Reset): Revert Tiling Shell extension to system defaults.
    - [x] `configure-text-editor-dev` (Deviation):
        - [x] Indentation: Spaces, 4 per tab/indent.
    - [x] `configure-text-editor-dewy-visuals` (Deviation):
        - [x] Dark Mode, Line Numbers, Overview Map, Highlight Current Line.
    - [x] `configure-text-editor-reset` (Reset): Revert indentation and visuals to system defaults.
    - [ ] figure out terminal recipes (starship/no starship, light theme/system theme, etc)
    - [x] `set-window-controls-right-full` (Deviation): Sets `:minimize,maximize,close`.
    - [x] `set-window-controls-right-gnome` (Deviation): Sets `:close`.
    - [x] `set-window-controls-left-gnome` (Reset): Sets `close:` (reverts to system default).
    - [x] `sort-app-grid` (Deviation): Removes folders and sorts alphabetically.
    - [ ] `default-app-grid` (Reset): Restores folders and sorts with default sorting.
    - [x] `preset-dock-gnome` (Reset): Reset to default Gnome Dash (dash in overview)
    - [ ] `_preset-dock-redfox` (Hybrid): TODO: A hacky stub of a recipe has been implemented; it works, but should be considered a proof of concept.
        - Default behavior will be to automatically switch between GNOME style dash and redfox style dock depending on monitor size (and scaling) -- this means we may need to create an additional recipe that sets the user to the default switching behavior and likely a systemd service to monitor monitor size(s)
        - The stub recipe requires logging out and logging in any time it is switched to or from
        - A true fix will likely involve forking (or getting a PR accepted with) Dash to Dock.
        - [ ] Don't disable overview on startup (in dash to dock) -- it's a nice touch starting up to the overview
        - [ ] Clock and Overview search should probably remain centered even if the usable workspace size changes
    - [x] `preset-dock-ubuntu` (Deviation): Configure Dash to Dock (Left side). Turn on Dash to Dock.
    - [ ] `preset-dock-win-classic` (Deviation): Configure Dash to Dock (Bottom, Taskbar style, icons on left). Turn on Dash to Dock.
    - [ ] `preset-dock-win-new` (Deviation): Configure Dash to Dock (Bottom, Taskbar style, icons on centered). Turn on Dash to Dock.
    - [ ] `preset-dock-macos` (Deviation): Configure Dash to Dock (Bottom, Floating). Turn on Dash to Dock.
    - [x] `configure-xway-scale-off` (Reset): Disable `xwayland-native-scaling`.
        - setting has changed. update based on xwayland-scaling-factor (default is off, i.e. xwayland-native-scaling is on, i.e. not the better setting for games)
    - [x] `configure-xway-scale-on` (Deviation): Enable `xwayland-native-scaling`.
        - setting has changed. update based on xwayland-scaling-factor (default is off, i.e. xwayland-native-scaling is on, i.e. not the better setting for games)
- [ ] **Hardware Atoms (Must include Host Checks):**
    - [x] `fix-oryp9-mouse`: Udev rule (Run only if Oryp9).
    - [x] `fix-acer-nouveau`: Kernel args (Run only if Acer).

### Level 1.5: Small-ecules (Software packs)
- [x] `install-productivity`: Flatpak list (Office, etc.).
    - [x] potentially also `install-daily`: this and productivity may be one unit or two. This would include things like Tuba, RSS feed reader, Audiobook reader, etc.
- [x] `install-music`: Flatpak list (Ardour, Musescore, Lilypond, Frescobaldi, etc.).
- [x] `install-creative`: Flatpak list (Blender, Krita, Inkscape, Photo stuff, GIMP, Kdenlive, OBS etc.).
- [x] `install-dev`: Combines `install-zed`, `setup-vscode`, `setup-cursor`, `install-gemini-cli` (gemini cli deprecated/removed).

### Level 2: Molecules (Logical Groups)
- [ ] **Software Bundles (Install Molecules):**
    - [x] `install-matt`: Combines `install-dev`, `install-music`, `install-creative`, `install-productivity`, and `install-daily` if it is created.
    - [x] `install-dewy`
    - [x] `install-normie`: Combines `install-productivity`, `install-creative`, and `install-daily` if it is created.
    - [ ] `install-fedora` (install at least all GNOME basics (might need to not use packs and just manually make a list))

- [ ] **Config Molecules (User/Tool Setup):**
    - [ ] `configure-matt`:
        - [x] Runs Hardware Atoms (Logic checks happen inside atoms or here).
        - [x] Runs `configure-xway-scale-off`.
        - [ ] Runs `configure-git`.
        - [ ] Runs `configure-heroic` (if configure-heroic remains a ujust recipe and not a system default)
    - [ ] `configure-dewy`:
        - [x] Runs `configure-xway-scale-on`.
        - [ ] **Task:** Determine configs and sub-recipes.
    - [ ] `configure-fedora`:
        - [x] Runs `configure-xway-scale-on`.
        - [ ] **Task:** Determine configs and sub-recipes.
    - [ ] `configure-normie`:
        - [x] Runs `configure-xway-scale-off`.
        - [ ] **Task:** Determine configs and sub-recipes.

- [ ] **Layout Molecules (UX/Behavior/Positioning):**
    - [ ] `layout-matt` (Renamed from theme-matt):
        - [x] runs `sort-app-grid`.
        - [x] runs `set-window-controls-left-gnome`.
    - [ ] `layout-dewy` (Renamed from theme-dewy):
        - [x] Runs `sort-app-grid`.
        - [x] Runs `set-window-controls-right-full`.
        - [x] Runs `preset-dock-ubuntu` (or custom Dewy dock settings).
    - [ ] `layout-fedora`: "Reset" recipe to restore Vanilla Fedora layout.
    - [ ] `layout-normie`: Flexible layout switcher?

- [ ] **Theme Molecules (Visuals/Assets):**
    - [ ] `theme-matt`: Sets wallpapers, GTK theme (Adwaita Dark), Icons.
    - [ ] `theme-dewy`: Sets wallpapers, GTK theme (Adwaita Light), Icons.
    - [ ] `theme-fedora`: Reset visuals to default.

### Level 3: Organisms (User Bootstraps)
- [ ] `bootstrap-matt`: Runs `install-matt`, `theme-matt`, `layout-matt`, `configure-matt`.
- [ ] `bootstrap-dewy`: Runs `install-dewy`, `theme-dewy`, `layout-dewy`, `configure-dewy`.
- [ ] `bootstrap-fedora`: Runs `theme-fedora`, `layout-fedora`, `configure-fedora` (no install-fedora).
- [ ] `bootstrap-normie`: Runs `install-normie`, `theme-normie`, `layout-normie`, `configure-normie`.

## 🛠️ Ujust Idempotency Fixes
- [x] **Research & Fix:** Identify and resolve recipes that fail or cause issues when run multiple times.
    - [x] `add-swap`: Idempotent; offers to recreate or skips if already active.
    - [x] `install-gemini-cli`: Fails if already installed via Homebrew. (No, this is fine as is--it's *supposed* to be installed via homebrew, and running this will update it) (gemini cli deprecated/removed)
    - [x] `uninstall-gemini-cli`: Fails if not installed. Now fixed. (deprecated/removed)
    - [x] `install-zed`: Should check for existing installation before running `curl | sh`. (No, this is not necessary; re-running will simply update it)
    - [x] `fix-oryp9-mouse`: Idempotent; checks if udev rule already exists and matches content.
    - [x] `configure-nordvpn`: Idempotent; `import-nord-configs` now deduplicates connections and always enforces sort order.

## 🎨 Branding & Aesthetics
- [ ] **Wallpapers**
    - [ ] Import all Bluefin / Bluefin DX wallpapers.
    - [ ] **Collection:** Gather Pawel Czerwinski Light/Dark pairs.
- [ ] **RedFoxOS Branding**
    - [ ] Create/Add assets: Neofetch/Fastfetch Logo, Splash Screen, System Info Logo.

## Fixups/New (Items that arrive after a fix is already implemented)
- [x] Screenshot (add Windows super + shift + s shortcut for selection screenshot; move fullscreen screenshot to printscreen)
- [x] Check that Boxes is installing as system package and is cross-compatible with VMM
- [x] Confirm that Winboat is best as app-image (RPM is published on github releases page, so we could be doing this as a system package; the issue is that the appimage setup is not frictionless).
    - [x] Test appimage to confirm is working. If not, try RPM. Proceed based on findings
    - [x] Winboat requires FreeRDP
- [x] Change names for everything (Completed: Renamed to RedFoxOS)
- [x] Add sound theme change -- ujust (set default sound theme to normal fedora default, "reset". set sound to bazzite, "deviation")
    - [x] Set system default override to 'freedesktop' (Fedora default).
    - [x] Create ujust recipes: `theme-sound-fedora` (reset) and `theme-sound-bazzite` (set to 'bazzite').
- [x] Dock defaults
- [x] Set default hostname, etc (Implemented via static file `files/system/etc/hostname`) -- wrong, need to take a second swing at it (and remove the first attempt) -- Did we get this right? I think we did, but we should determine that and say so if so
- [ ] Cursor Remote Tunnels fixes from AmyOS
- [ ] vesktop icons fix (would like to use discord icons in system tray, perhaps different app icon too)
- [ ] Android studio (add copr repo and package to main recipe) -- Not sure I want to keep this one (there are other methods than baking it in, including brew casks or whatever theyre called; there's one for jetbrains; there's also a ujust that does basically the same thing--both have a pathing issue that needs a workaround on systems with the whole /var/home/ setup)
- [ ] Bake Ollama
- [ ] implement 6 openclaw recipes (installs for openclaw, openclaw orchestrator, openclaw worker, and uninstalls for openclaw, orchestrator, and worker) -- see standalone to-do doc
- [ ] rounded blur issue in blur my shell


## Running Matt fixes
- [ ] Post-GNOME Builder install fix to reset file associations (GNOME builder steals just about any type of code file, python, json, sh, etc.)
- [x] Text Editor should not open previous session by default

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
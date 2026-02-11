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
- [ ] **Dash to Dock (Disabled by default, but configured)**
    - [ ] **Behavior:** Isolate Workspaces (`true`).
    - [ ] **Click Action:** `minimize-or-previews` (Focus, minimize, or show previews).
    - [ ] **Size:** Fixed icon size (Scroll to reveal).
    - [ ] **Size:** Icon size limit (40px).
    - [ ] **Appearance:** Shrink the dash (remove edge-to-edge).
- [ ] **App Grid Defaults**
    - [ ] **Behavior:** Sort alphabetically (no folders).
        - [ ] Add behavior to keep user's folders saved, so they can go back to them if they want
    - [ ] **Behavior:** Pinning to dock must not remove from grid.

## 📦 Default Software
- [x] **Winboat:** Determine installation (DNF/Flatpak) and add to system defaults.
- [ ] **Dropbox:** Install official Dropbox client (System/DNF/RPM)
    - [x] Remove maestral after dropbox is tested and experience is satisfactory (if maestral is not removed, improve maestral uninstall script to remove leftovers)
- [x] **Implement** System-level GNOME Boxes + Virt-Manager
- [ ] **Implement** Starship terminal prompt by default with light-theme terminal (steal from Bluefin)
    - [ ] **Implement** ujust "configure" recipes for starship bluefin (system default, "reset"), starship bazzite (deviation), starship off (deviation)

## 🌳 The `ujust` Architecture Tree
*The master plan for `files/system/usr/share/ublue-os/just/99-redfox.just`.*

> **Architecture Note: Deviations vs. Resets**
> *   **Deviation Recipes** (e.g., `set-window-controls-right`) use `gsettings set` to apply specific user preferences.
> *   **Reset/Default Recipes** (e.g., `set-window-controls-left-gnome`) use `gsettings reset` to clear user overrides and revert to the system-wide baseline defined in `gschema-overrides`.

### Level 1: Atoms (Single-Purpose Scripts)
- [ ] `configure-git`: Interactive setup (User/Email/SSH) using `gh` CLI.
- [ ] `setup-vscode`:
    - [ ] **Task:** Compile final list of extensions.
    - [ ] **Task:** Implement `jq` script to inject settings (Theme, Fonts, etc.).
- [ ] `setup-cursor`: Mirror `setup-vscode` logic.
- [x] `install-zed`: Script to install Zed via `curl | sh` to `~/.local`.
- [x] `install-gemini-cli`: `brew install gemini-cli`.
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
    - [ ] `sort-app-grid` (Deviation): Removes folders and sorts alphabetically.
    - [ ] `default-app-grid` (Reset): Restores folders and sorts with default sorting.
    - [ ] `preset-dock-ubuntu` (Reset): Configure Dash to Dock (Left side). Turn on Dash to Dock.
    - [ ] `preset-dock-win-classic` (Deviation): Configure Dash to Dock (Bottom, Taskbar style, icons on left). Turn on Dash to Dock.
    - [ ] `preset-dock-win-new` (Deviation): Configure Dash to Dock (Bottom, Taskbar style, icons on centered). Turn on Dash to Dock.
    - [ ] `preset-dock-macos` (Deviation): Configure Dash to Dock (Bottom, Floating). Turn on Dash to Dock.
- [ ] **Hardware Atoms (Must include Host Checks):**
    - [ ] `fix-oryp9-mouse`: Udev rule (Run only if Oryp9).
    - [ ] `fix-acer-nouveau`: Kernel args (Run only if Acer).
    - [ ] `fix-4k-scaling`: Remove `xwayland-native-scaling`.

### Level 1.5: Small-ecules (Software packs)
- [x] `install-productivity`: Flatpak list (Office, etc.).
    - [x] potentially also `install-daily`: this and productivity may be one unit or two. This would include things like Tuba, RSS feed reader, Audiobook reader, etc.
- [x] `install-music`: Flatpak list (Ardour, Musescore, Lilypond, Frescobaldi, etc.).
- [x] `install-creative`: Flatpak list (Blender, Krita, Inkscape, Photo stuff, GIMP, Kdenlive, OBS etc.).
- [x] `install-dev`: Combines `install-zed`, `setup-vscode`, `setup-cursor`, `install-gemini-cli`.

### Level 2: Molecules (Logical Groups)
- [ ] **Software Bundles (Install Molecules):**
    - [x] `install-matt`: Combines `install-dev`, `install-music`, `install-creative`, `install-productivity`, and `install-daily` if it is created.
    - [x] `install-dewy`
    - [x] `install-normie`: Combines `install-productivity`, `install-creative`, and `install-daily` if it is created.
    - [ ] `install-fedora` (install at least all GNOME basics (might need to not use packs and just manually make a list))

- [ ] **Config Molecules (User/Tool Setup):**
    - [ ] `configure-matt`:
        - [ ] Runs Hardware Atoms (Logic checks happen inside atoms or here).
        - [ ] Runs `configure-git`.
        - [ ] Runs `configure-heroic` (if configure-heroic remains a ujust recipe and not a system default)
    - [ ] `configure-dewy`:
        - [ ] **Task:** Determine configs and sub-recipes.
    - [ ] `configure-fedora`:
        - [ ] **Task:** Determine configs and sub-recipes.
    - [ ] `configure-normie`:
        - [ ] **Task:** Determine configs and sub-recipes.

- [ ] **Layout Molecules (UX/Behavior/Positioning):**
    - [ ] `layout-matt` (Renamed from theme-matt):
        - [ ] runs `sort-app-grid`.
        - [ ] runs `set-window-controls-left-gnome`.
    - [ ] `layout-dewy` (Renamed from theme-dewy):
        - [ ] Runs `sort-app-grid`.
        - [ ] Runs `set-window-controls-right-full`.
        - [ ] Runs `preset-dock-ubuntu` (or custom Dewy dock settings).
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
- [ ] Dock defaults
- [x] Set default hostname, etc (Implemented via static file `files/system/etc/hostname`) -- wrong, need to take a second swing at it (and remove the first attempt)
- [ ] Cursor Remote Tunnels fixes from AmyOS
- [ ] vesktop icons fix (would like to use discord icons in system tray, perhaps different app icon too)

## Running Dewy fixes
- [x] System Dropbox
- [x] Cursor ruff extension (in ujust)
    - cursor --install-extension charliermarsh.ruff --force
- [x] cursor dark modern theme
- [x] texlive auto select version (latest)
- [x] tray defaults (files, mission center, settings, terminal, firefox, brave, calculator, text editor, zed, cursor, spotify, slack, signal, vesktop
- [x] brave in install-dewy
- [x] slack in install-dewy
- [ ] square window corners (in as many situations as possible--libadwaita, gtk3, flatpak, etc.)

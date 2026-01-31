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

## 📦 Default Software
- [x] **Winboat:** Determine installation (DNF/Flatpak) and add to system defaults.
- [x] **Implement** System-level GNOME Boxes + Virt-Manager
- [ ] **Implement** Starship terminal prompt by default with light-theme terminal (steal from Bluefin)

## 🌳 The `ujust` Architecture Tree
*The master plan for `files/system/usr/share/ublue-os/just/99-redfox.just`.*

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
    - [ ] figure out terminal recipes (starship/no starship, light theme/system theme, etc)
    - [ ] `set-window-controls-right`: Sets `:minimize,maximize,close`.
    - [ ] `set-window-controls-left-gnome`: Sets `close:`. (this is the default, but it needs to exist if someone runs the above and wants to return to default without nuking their whole dconf file)
    - [ ] `sort-app-grid`: Removes folders and sorts alphabetically.
    - [ ] `default-app-grid`: Restores folders and sorts with default sorting. (this is the default, but like the above, it needs to exist)
    - [ ] `preset-dock-ubuntu`: Configure Dash to Dock (Left side). Turn on Dash to Dock.
    - [ ] `preset-dock-win-classic`: Configure Dash to Dock (Bottom, Taskbar style, icons on left). Turn on Dash to Dock.
    - [ ] `preset-dock-win-new`: Configure Dash to Dock (Bottom, Taskbar style, icons on centered). Turn on Dash to Dock.
    - [ ] `preset-dock-macos`: Configure Dash to Dock (Bottom, Floating). Turn on Dash to Dock.
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
- [ ] **Software Bundles:**
    - [x] `install-matt`: Combines `install-dev`, `install-music`, `install-creative`, `install-productivity`, and `install-daily` if it is created.
    - [x] `install-dewy`
    - [x] `install-normie`: Combines `install-productivity`, `install-creative`, and `install-daily` if it is created.

- [ ] **Theme Molecules:**
    - [ ] `theme-matt`
        - [ ] runs `sort-app-grid`.
        - [ ] runs `set-window-controls-left-gnome`.
    - [ ] `theme-dewy`:
        - [ ] Runs `sort-app-grid`.
        - [ ] Runs `set-window-controls-right`.
        - [ ] Runs `preset-dock-ubuntu` (or custom Dewy dock settings).
    - [ ] `theme-fedora`: "Reset" recipe to restore Vanilla Fedora look.
- [ ] **Config Molecules:**
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

### Level 3: Organisms (User Bootstraps)
- [ ] `bootstrap-matt`: Runs `install-matt`, `theme-matt`, `configure-matt`.
- [ ] `bootstrap-dewy`: Runs `install-dewy`, `theme-dewy`, `configure-dewy`.
- [ ] `bootstrap-fedora`: Runs `theme-fedora`, `configure-fedora` (no install-fedora; all main default fedora apps should already be installed)
- [ ] `bootstrap-normie`: Runs `install-normie`, `theme-normie`, `configure-normie`.

## 🎨 Branding & Aesthetics
- [ ] **Wallpapers**
    - [ ] Import all Bluefin / Bluefin DX wallpapers.
    - [ ] **Collection:** Gather Pawel Czerwinski Light/Dark pairs.
- [ ] **RedFoxOS Branding**
    - [ ] Create/Add assets: Neofetch/Fastfetch Logo, Splash Screen, System Info Logo.

## Fixups/New (Items that arrive after a fix is already implemented)
- [ ] Screenshot (add Windows super + shift + s shortcut for selection screenshot; move fullscreen screenshot to printscreen)
- [x] Check that Boxes is installing as system package and is cross-compatible with VMM
- [x] Confirm that Winboat is best as app-image (RPM is published on github releases page, so we could be doing this as a system package; the issue is that the appimage setup is not frictionless).
    - [x] Test appimage to confirm is working. If not, try RPM. Proceed based on findings
    - [x] Winboat requires FreeRDP
- [x] Change names for everything (Completed: Renamed to RedFoxOS)
- [ ] Add sound theme change
- [ ] Dock defaults
- [ ] Set default hostname, etc

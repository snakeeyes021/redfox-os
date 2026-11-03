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
- [x] **Tailscale:** add to system defaults. *(Already there: Bazzite ships Tailscale, off until you run `ujust tailscale enable`. Nothing to change.)*
- [ ] **Remove Winboat** from the defaults (reverses the Winboat item above). *(On `feat/small-roadmap-items`: out of `install-compatibility`; `install-winboat` stays opt-in.)*
- [ ] **Replace Mission Center** (slow to start, frozen at first, heavy on memory) with a better system monitor. *(On `feat/system-monitor`: Resources, `net.nokyan.Resources`, for new setups and the Dewy dock; Ctrl+Shift+Esc, Ctrl+Alt+Del on the keypad and Logo Menu's button open it through `redfox-system-monitor`, which falls back to Mission Center where that's all there is. Existing installs keep Mission Center.)*
- [ ] **VS Code:** install the Antigravity extension. *(On `feat/small-roadmap-items`: `Google.google-antigravity`.)*
- [ ] **Implement** Starship terminal prompt by default with light-theme terminal (steal from Bluefin)
    - [ ] **Implement** ujust "configure" recipes for starship bluefin (system default, "reset"), starship bazzite (deviation), starship off (deviation)

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
    - [x] `configure-xway-scale-off` (Reset): Disable `xwayland-native-scaling` (reverts factor to default).
    - [x] `configure-xway-scale-on` (Deviation): Enable `xwayland-native-scaling` (forces factor to 0.0).
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

## 🪟 Layout Modes
*Built on `feat/layout-modes` and tested live in the VM; waiting for Matt's check before merging. `redfox-layout list/get/set` switches between gnome, ubuntu, macos, windows-classic, windows and redfox without a logout, and the `preset-dock-*` recipes call it. Windows layouts use Dash to Panel + ArcMenu. The restart had two causes: the gap hack copied Dash to Dock into `~/.local`, which GNOME only picks up at login; and smooth-overview broke when GNOME called enable() or disable() twice in a row ("too much recursion"), leaving the overview broken until the shell restarted.*
- [ ] **Layout names without other systems' names** (no Windows, macOS or Ubuntu where people see them). *(Proposal with SVG previews in [`docs/layout-names.md`](layout-names.md) on `feat/layout-modes`; waiting for Matt to pick.)*
- [ ] **More layouts, built from scratch:** today only the Ubuntu-style layout (and Dewy's variant) is finished. Build the rest of the presets above (`preset-dock-win-classic`, `preset-dock-win-new`, `preset-dock-macos`, the `_preset-dock-redfox` hybrid proof of concept) plus any others we want. Zorin's layouts are Zorin Pro (paid): don't consult or look at their implementation.
- [ ] **Switching layouts works live:** moving between presets shouldn't need a logout or restart. Some switches depend on smooth-overview, and something there may need a restart (possibly because the extension is built from source at image build time: `files/scripts/install-smooth-overview.sh`). Find out and fix it.
- [ ] **smooth-overview, hardened:** *(Done on smooth-overview's local `harden` branch, not pushed yet: InjectionManager, safe to enable/disable twice, only the overview's and top bar's own lookups change, keeps the clock centred. Publishing on extensions.gnome.org needs Matt's account.)* review it against GNOME Shell extension best practice (it was thrown together quickly), make sure it's solid on the current GNOME, install it the proper way for a system extension, and consider publishing it on extensions.gnome.org.

## 🧩 RedFox Hub (Flatpak GUI)
*Design: [`docs/redfox-apps-design.md`](redfox-apps-design.md). Matt decided on one app, **RedFox Hub** (`tech.redfoxlabs.Hub`), a Flatpak released like Thirties and Pianola, with four sections. Building starts after Matt's branch review.*

Move RedFox's own tooling into one GUI Flatpak app, like Thirties and Pianola already are (`tech.redfoxlabs.*`):
- [ ] **Welcome:** a short, cheerful tour of RedFoxOS at first login, in the spirit of GNOME Tour, ending in links to Apps, Settings and the Manual. Runs after Bazzite Portal; a first-login step fetches Hub.
- [ ] **Settings:** a front end to `redfox-config` / `config.yaml` and RedFox's settings, services and actions (see the setup-GUIs item in Fixups), including the layout picker with the RedFox layout names and previews.
- [ ] **Apps:** a checklist of software and bundles (the `install-*` packs); tick and it installs them.
- [ ] **Manual:** a very short help guide, only for where RedFoxOS differs from mainline Linux (it's immutable) or from other immutable distros (the conveniences and tools we chose). For example: "I want to install a Flatpak / a CLI tool, what do I do?", "My collaborators and I need identical dev setups with a specific Node version", "I need a Python environment; what are my options?" (uv, and whatever else we provide).

## 🧰 Editors
- [ ] **Dewy and Sloppy extensions by default:** *(On `feat/small-roadmap-items`, in the `90-vscode.sh` login hook; Cursor's marketplace returns 403 for both, so it falls back to the Open VSX `.vsix`.)* install `RedFoxLabs.dewy` and `RedFoxLabs.sloppy` (on both the VS Code Marketplace and Open VSX) in VS Code and every fork we ship or set up (Cursor, Antigravity, etc.): add to `setup-vscode` / `setup-cursor`.

## 🧪 Testing
- [ ] **VM testbed:** `tests/vm/` (on `feat/layout-modes`) builds a Bazzite VM, `redfox-test`, and documents the three ways to test a feature branch: a hotfix overlay, a local `bluebuild build` plus rebase, or CI's `pr-*` images.
- [ ] **Rebase from elsewhere now and then:** we normally rebase from Bazzite. Occasionally test rebasing from Bluefin (and other uBlue images) to make sure our setup holds up. Not pressing.
    - [x] Bluefin → RedFox, 2026-11-01: works; details in `tests/vm/README.md` (on `feat/layout-modes`). It takes about 45 min, since the images share no layers. It found that the `docker` group never reaches a rebased machine (Bazzite too), so `docker.socket` fails; fixed on `fix/docker-group-after-rebase`. Bluefin-only extensions (Search Light, Logo Menu) disappear without a message, and some packages drop a version until the next update.

## 🔐 User Config, Secrets & the ujust Audit
- [ ] **One secrets/config note per user:** the user keeps a single note in their secrets manager (Bitwarden or similar) that is their `~/.config/redfox/config.yaml`. It holds the settings that belong to the user rather than the OS, plus every secret or sensitive value, and RedFox sets everything else up from it automatically. Only a few integrations read it so far (NordVPN, per-machine hostname and quirks); audit which still need wiring.
- [ ] **API keys for agents and tools:** keys (Gemini, Anthropic, OpenAI, etc.) come from the config, and RedFox puts each where its tool expects it (keyring or environment) instead of hand-editing `.bashrc`. A Gemini API key is still in the hp machine's `.bashrc`. Agent harness sign-ins (Claude Code, agy, T3, `gh`) stay a one-time prompt on first run unless the user goes the API-key route.
- [ ] **Agent CLI themes:** *(Claude Code part on `feat/small-roadmap-items`: its `auto` theme follows the terminal, set at login when no theme is chosen. agy still to do: it has a `colorScheme` setting and `--settings`, but no auto mode found yet.)* Terminal agents (Claude Code, agy, etc.) need a dark theme in the terminal but a light one inside VS Code. Pick defaults that follow where they're running.
- [ ] **Audit the ujust recipes:** for each one, decide whether it belongs in the OS or is one user's quirk that should move into that user's config. Some stay baked in on purpose: `bootstrap-matt` and `bootstrap-dewy` are a nice touch, since RedFox is two brothers.

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
    - [ ] **Collection:** Gather Pawel Czerwinski Light/Dark pairs.
- [ ] **RedFoxOS Branding:** the OS calls itself RedFoxOS, not Bazzite, everywhere a person sees it. Machine-readable IDs that tooling reads stay Bazzite's; the trade-offs are in `docs/branding.md`. *(Built and tested in the VM on `feat/branding`, including update, rollback and rebase; waiting for Matt's OK to merge. Ticked items are done on that branch.)*
    - [x] `os-release`: NAME/PRETTY_NAME "RedFoxOS", LOGO, URLs, DEFAULT_HOSTNAME `redfox`, BOOTLOADER_NAME, IMAGE_ID. `ID=bazzite` is kept.
    - [x] `image-info.json`: image name, vendor and ref are RedFox's (for the MOTD and Bazzite's scripts).
    - [x] Settings → About: name and logo (light and dark variants).
    - [x] GRUB entries: "RedFoxOS (ostree:N)".
    - [x] Login screen (GDM) logo: larger, light lettering for the dark background.
    - [x] Boot splash (Plymouth): RedFox watermark, larger and legible. It never showed before, because the initramfs kept Bazzite's copy; the build now rebuilds it.
    - [x] Fastfetch: RedFox fox in RedFox red, and the real booted image ref.
    - [x] Starship: a RedFox default config with a 🦊 OS symbol (Starship itself is the separate Starship item).
    - [x] Terminal banner (MOTD): RedFox welcome, links and tips; Bazzite's tips removed.
    - [x] Fedora logo files (installer, initial setup, About dialogs) regenerated from the RedFox art.
    - [ ] Bazzite Portal and Bazzite Announcements stay as they are: their content is Bazzite's. RedFox Hub's Welcome runs after the Portal for now (whether to replace it is still open).
    - [x] Bazzite's rollback helper (`bazzite-rollback-helper`, `bruh`) only knows Bazzite images. *(`redfox-rollback-helper` / `ujust rollback-helper` on `feat/redfox-rollback-helper`: lists builds of latest/unstable by commit and date, rolls back, rebases with a warning when switching NVIDIA flavour. Tested in the VM.)*
    - [x] Create/Add assets: Neofetch/Fastfetch Logo, Splash Screen, System Info Logo. *(Made from the existing art by `assets/branding/make-images.py` on `feat/branding`.)*
    - [ ] **New artwork from Matt** (listed in `docs/branding.md`): the fox as an SVG; a simple single-colour fox mark for 16 px and symbolic icons (ArcMenu's start button, Logo Menu); the wordmark as a vector, or its font.
    - [ ] **Fox-face mark:** a simple, flat fox face for small sizes, used for the fastfetch logo (bigger than today's), ArcMenu's start button and the Logo Menu (white, symbolic), and 16–32 px icons. *(Two drafts are waiting for Matt to pick one: `~/Pictures/redfox-fox-face/`.)*
    - [ ] **Commission a human artist** (e.g. on Fiverr) to paint the watercolour fox properly, and probably to redraw the face mark and the wordmark as vectors at the same time. Until then the current fox stays.

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
- [ ] Joplin and Signal start minimized to the tray, but only when started at boot; started any other way they open normally. *(On `feat/small-roadmap-items`: `ujust configure-autostart-tray`, run by `configure-matt`.)*
- [ ] Mailspring doesn't get Adwaita as its default theme, but it should. *(Matt chose to write our own. On `feat/mailspring-adwaita`: RedFox Adwaita Light and Dark, written from scratch, used by Mailspring's Automatic theme so it follows GNOME's light/dark setting and accent colour. A GNOME front end over Mailspring's sync engine was looked at and isn't recommended: [`docs/mailspring-gnome-frontend.md`](mailspring-gnome-frontend.md).)*
- [ ] Setup/bootstrapping/config GUIs for managing RedFox's app sets, settings, services, actions, etc.
- [ ] Midikeep: GNOME notifications don't group.
- [ ] Midikeep: let the user set where the session archive goes, in a config Pianola also reads (Pianola side is in its `docs/BACKLOG.md`).


## Running Matt fixes
- [ ] Post-GNOME Builder install fix to reset file associations (GNOME builder steals just about any type of code file, python, json, sh, etc.)
- [x] Text Editor should not open previous session by default
- From the Joplin note "RedfoxOS Manual Steps" (done by hand on Matt's machine; automate):
    - [ ] Install T3
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
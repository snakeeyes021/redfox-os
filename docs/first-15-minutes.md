# The first 15 minutes of a new RedFoxOS user

A walk through a brand-new install of `ghcr.io/snakeeyes021/redfox-os:unstable`, done on 2026-11-04 in the `redfox-fresh` VM.

Screenshots are in `/var/home/matt/previews/first-15/`.

## How it was installed

There is no RedFox ISO yet. The image was installed straight from the Silverblue installer with `tests/vm/create-vm.sh` (6 GB of memory, 1280×800 screen). The account was made the way Bazzite's installer makes it: `alex`, in `wheel`, with a password, no autologin and no passwordless sudo. `VM_FRESH=1` does this; it is on the branch `test/fresh-install-vm`.

GNOME Initial Setup isn't part of RedFoxOS. Bazzite doesn't ship `gnome-initial-setup`, and its installer creates the account. Installed with no account, the machine stops at a login screen nobody can get past (`01-gdm-no-account.png`). So a RedFox ISO must create the account in the installer, as Bazzite's does.

Two baselines are kept next to the VM's disk, both shut off:

- `redfox-fresh-baseline.qcow2`: straight after the install, before first boot, with no account.
- `redfox-fresh-account-baseline.qcow2`: after first boot, with `alex` added and `rhgb quiet` set, before the first login. Start here to repeat the walk.

The VM's own disk is left as the walk ended: updated, with Signal installed.

## What a new user sees, in order

1. **Boot.** GRUB says "RedFoxOS (ostree:0)" (`00-firstboot-grub.png`, `02-grub-menu.png`). The splash shows the RedFoxOS watermark (`04-boot-splash.png`); the logo above it is the VM's firmware logo.
2. **First boot restarts by itself.** About three minutes in, Bazzite's hardware setup adds a kernel argument and reboots the machine. The screen says "Preparing System - Please wait, this may take a while" while it runs.
3. **Login screen.** RedFoxOS lettering, the user's name (`03-gdm.png`). Fine.
4. **First login.** Three things open by themselves (`06-first-login-portal-steam.png`):
   - Bazzite Portal, with "Launch at startup" on;
   - Steam: "Steam is opening for the first time", then a 240 MB download, then its sign-in window;
   - a notification, "Changes to Fcitx5 on Bazzite", that stays until it's dismissed.
   It starts in the overview. At 1280×800 there is no dock on the desktop, only the GNOME dash in the overview (`10-desktop-empty.png`, `11-overview.png`).
5. **Terminal.** The welcome message says RedFoxOS and links RedFox's issues, docs and site (`12-terminal-motd.png`).
6. **App grid.** Two pages (`13-app-grid-1.png`, `14-app-grid-2.png`).
7. **Bazaar.** About a minute of "Refreshing" the first time (`17-bazaar-refreshing.png`), then it works. Signal installed in 32 seconds with no password prompt (`20-bazaar-signal-installed.png`).
8. **Signal.** Opened straight to its link-a-phone screen, with no keyring warning (`21-signal-first-start.png`).
9. **First update.** `ujust update` pulled a newer image (2.4 GB) and finished in about 13 minutes with a clear summary and a reboot prompt (`22-ujust-update-done.png`). uupd, run by hand, took 4.5 minutes and staged the next image without a word.
10. **Settings.** About shows the RedFoxOS logo and name, and the hostname `redfox` (`25-settings-about-light.png`). Dark mode switches the shell, Settings, Bazaar and the terminal (`29-appearance-dark.png`, `30-dark-apps.png`).
11. **Second login.** The Portal, Steam's sign-in window and the Fcitx5 notification all come back (`31-second-login.png`).
12. **Firefox.** Its usual first-run screen (`32-firefox-first-start.png`).

Mailspring, Signal and Joplin aren't installed by default (`recipes/_common-modules.yml`), so only Signal was tried, after installing it.

## Findings

### Fixed

**libvirt never started on a fresh install.** `virt-secret-init-encryption.service` failed at every boot. It writes its key into `/var/lib/libvirt/secrets`, which nothing creates on a fresh ostree install, and `libvirtd` requires it. So virt-manager couldn't connect to `qemu:///system`. This is new with libvirt 12.6 in the Fedora 45 base.
- Fix: a tmpfiles.d entry creates the folder.
- Tested: no failed units after a reboot, the key was made, and `virsh -c qemu:///system` listed the default network. The next CI image carried it, and that boot had no failed units either.
- Status: fixed on `fix/libvirt-secrets-dir`, merged (fc43ec4).

**Every `ujust update` started with an error.** "ERROR Unable to read /etc/ublue-os/topgrade.toml: No such file or directory" (`23-ujust-update-topgrade-error.png`). RedFox's topgrade settings include that file, but Bazzite's Fedora 45 images no longer ship it. On Fedora 44 it held Bazzite's Mozilla theme and CSS loader update steps, whose scripts are gone too.
- Fix: the include is dropped.
- Tested: `topgrade --dry-run` with the new settings runs the same steps with no error.
- Status: fixed on `fix/topgrade-missing-include`, merged (75e106f).

**The terminal tip names layouts that no longer exist.** "`redfox-layout set macos` switches without logging out", and it lists "macOS, Windows". Those names were replaced by Cal, Wash and Nostalgia, and `redfox-layout set macos` fails. The layouts row in the table also wrapped in a new 80-column terminal, leaving a lone ")" on its own line (`12-terminal-motd.png`).
- Fix: the tip uses the current names, and the row is shorter.
- Tested: rendered at 80 columns in the VM; `redfox-layout set cal` works.
- Status: fixed on `fix/motd-layout-tip`, merged (98e7103).

**Swedish users got Bazzite's terminal banner.** "Välkommen till Bazzite", with Bazzite's issue tracker, docs, Discord and Bluesky.
- Fix: `branding.sh` points `template.sv.md` at RedFox's template.
- Tested: with `LANG=sv_SE.UTF-8`, the banner is RedFox's.
- Status: fixed on `fix/motd-swedish-template`, merged (87c211f).

### For Matt

Each of these is a choice, not a bug, so nothing was changed.

1. **Steam starts at every login.** On first login it shows a "first time" dialog, downloads 240 MB, then puts its sign-in window in front of whatever you're doing. It does this again at every login (`09-steam-firstrun.png`, `16-steam-signin-popup.png`, `31-second-login.png`). It comes from Bazzite's `~/.config/autostart/steam.desktop`. *Recommendation:* don't autostart Steam on RedFoxOS. Let the Hub offer it. *Status (11-04):* asked Matt.
2. **Bazzite Portal opens at every login.** Its pages are Bazzite's: Bazzite docs, Discord, Reddit, "Manage Bazzite", and a gaming-first app list. That list offers Antigravity and Android Platform Tools through Brew, which RedFox already ships (`07-bazzite-portal.png`, `08-portal-install-apps.png`). *Recommendation:* keep it until the Hub's Welcome is ready, then replace it. Turning its autostart off now would leave new users with nothing. *Status (11-04):* asked Matt; the Hub's Welcome now opens after it.
3. **Bazzite announcements.** "Changes to Fcitx5 on Bazzite" pops up on first login and stays at every login until it's dismissed (`06-first-login-portal-steam.png`). *Recommendation:* turn off `bazzite-announcement.desktop`, or filter it to announcements that matter to RedFox. *Status:* fixed (b0defcb): Bazzite's announcement messages are removed at build; the mechanism stays for RedFox's own.
4. **The default dock is Bazzite's.** It pins Firefox, Steam, Lutris, Bazaar, Bazzite Portal, Terminal and Files (`11-overview.png`). RedFox sets no `favorite-apps` of its own. *Recommendation:* pick RedFox's own set: Files, Firefox, Terminal, Bazaar, Text Editor, Settings, Resources. *Status (11-04):* asked Matt.
5. **New users get the plain GNOME layout.** `redfox-layout get` says `gnome`, though "RedFox" comes first in `redfox-layout list`. At 1280×800 this means an empty desktop with no dock (`10-desktop-empty.png`). *Recommendation:* decide which layout a new user should start in. The Hub's Welcome could ask. *Status (11-04):* asked Matt (recommended: RedFox).
6. **Pinned apps vanish from the app grid.** Firefox, Bazaar and Steam aren't in the grid while they're in the dock. The Alphabetical App Grid and Keep Pinned Apps extensions are installed but only turned on by `ujust sort-app-grid`. This is the open "App Grid Defaults" roadmap item (`13-app-grid-1.png`).
7. **The wallpaper picker has about 60 wallpapers.** They are Bazzite's, Fedora's and GNOME's, including 14 Steam Deck logos, "Tarkov pills" and "Troll". RedFox's own sits in the middle (`27-wallpaper-picker-scroll.png`, `28-wallpaper-picker-top.png`). *Recommendation:* remove the Steam Deck and Bazzite gaming wallpapers at build time, or at least list RedFox's first. *Status:* fixed (b0defcb): the wallpapers no GNOME or Fedora package ships are removed at build (Steam Deck logos, VGUI2, Troll, Bazzite, uBlue, convergence, giants, penguins). "Tarkov pills" is GNOME's own and stays. RedFox's is first (d5ccca9): Settings sorts by name with "Default Background" first, so RedFox's has that name and GNOME's is renamed "Adwaita". Checked on a fresh install.
8. **Bazaar's Curated page is gaming-first.** "Gaming: Protocol 3: Protect the Pilot", then ProtonPlus, Heroic and so on (`19-bazaar-curated.png`). It's Bazzite's curation. *Recommendation:* RedFox's own curated list, if Bazaar allows it. *Status (11-04):* asked Matt (`/usr/share/ublue-os/bazaar/content.yaml` can be replaced).
9. **The update's changelog is Bazzite's.** "[c]hangelog" after `ujust update` shows Bazzite's release notes, with "bazzite-rollback-helper rebase stable" (`24-update-changelog-bazzite.png`). RedFox has no release notes of its own. *Recommendation:* show RedFox's commits since the booted image, then Bazzite's notes under a heading saying they're the base's. *Status:* fixed (b0defcb): `redfox-changelog` shows RedFoxOS's own GitHub releases; the update menu offers "[c]hangelog" only when there are notes.
10. **The default extension list names one that isn't installed.** `zz99-redfox.gschema.override` enables `restartto@tiagoporsch.github.io` (Restart To). Bazzite's Fedora 44 image shipped it; Fedora 45 doesn't. It does no harm. *Recommendation:* ship it from extensions.gnome.org if you want it, otherwise drop it from the list. *Status:* fixed (b0defcb): dropped from the list; extensions.gnome.org has no GNOME 51 version of it.
11. **Antigravity IDE fails two extensions at every login.** `90-vscode.sh` tries `ms-vscode-remote.remote-containers` and `remote-ssh` in Antigravity IDE. Microsoft doesn't publish them to Open VSX, so both 404 at every login (in the journal only). *Recommendation:* use the open equivalents (`jeanp413.open-remote-ssh`), or drop them for Antigravity. *Status:* fixed (b0defcb): dropped for Antigravity. Cursor also reinstalled them at every login (it uses its own `anysphere.remote-*`); fixed too.
12. **First boot reboots by itself.** Bazzite's hardware setup sets a kernel argument and restarts, about three minutes into first boot. A new user might think it crashed. A RedFox ISO could set the argument at install time instead. *Status:* fixed (b0defcb) for most machines: the argument is `bluetooth.disable_ertm=1`, now shipped in `/usr/lib/bootc/kargs.d`, so the setup has nothing to change. Machines that need hardware-specific arguments (AMD GPU, handhelds, Surface) still restart once. Confirmed on a fresh install of `:unstable`: the setup said "No karg changes needed" and the first boot carried on.
13. **GRUB's two entries look the same.** "RedFoxOS (ostree:0)" and "RedFoxOS (ostree:1)" carry no version or date (`02-grub-menu.png`). Same as Bazzite. *Status:* fixed (b0defcb): entries read "RedFoxOS 2026-11-04 20:31 (ostree:0)", the build's date and time.

Small things, seen and left alone:

- `tuned-ppd` failed once, on the very first boot (TuneD answered D-Bus too slowly). It didn't happen again.
- At login, Bazzite's user setup logs "The value for the SHELL variable was not found in the /etc/shells file" for the login screen's user. Harmless.
- In dark mode, Signal's message area stayed white until Signal was restarted.
- Signal's first start left its database key in plain text next to the encrypted one; the second start removed it.

### For the Hub's first-login Welcome

What the first 15 minutes showed a Welcome should cover:

- **Replace Bazzite Portal**, and say so once: RedFox's docs, issues and site, not Bazzite's Discord and docs.
- **Explain the first-boot restart** for anyone who sees it, or at least not surprise them after it.
- **Pick a layout.** New users start in plain GNOME, and on small screens there's no dock at all. The picker previews are ready (`assets/layouts/`).
- **Light or dark, accent, wallpaper.** RedFox's wallpaper is hard to find in Settings.
- **Optional apps, off by default:** Steam (instead of autostarting it), Signal, Mailspring, Joplin, with their "start in tray at login" toggles, and the software packs (`ujust install-productivity` and the rest).
- **Updates.** uupd works silently: it checks daily at 4am and stages the new image for the next restart, with no notification before or after. The Welcome should say so, and the Hub's Updates page should show when a restart is pending. `ujust update` and RedFox Updater do it now.
- **Bazaar.** Point to it as the place for apps, ideally with RedFox's own picks rather than the gaming-first Curated page.
- **Turning it off.** One clear "Don't show again", since the Portal's "Launch at startup" toggle is easy to miss.

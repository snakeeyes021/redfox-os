# Branches waiting for review

Status: eight RedFox branches, all pushed to GitHub and none merged yet. smooth-overview's `harden` is merged (item 1). Pushing them builds nothing: images build only from `main` and `unstable` (and PRs into them).

Each section below has:
- a short summary;
- the GitHub compare link (the branch's changes against `unstable`);
- the files worth reading;
- the screenshots.

Screenshots are on the tailnet preview, `https://redmax.taila6a47f.ts.net:8401/<name>`.

How they were tested, in the `redfox-test` VM:
- Branches 2–6 were built into one image together with `harden` and smoke-tested.
- Later changes, and branches 7–9, were tested by copying them over that image.
- All eight merge cleanly onto today's `unstable` (checked by merging them in order in a scratch copy).

## Suggested merge order

1. smooth-overview `harden` (its own repo; `feat/layout-modes` needs it). **Merged 2026-11-03.**
2. `fix/docker-group-after-rebase`
3. `feat/midikeep-data-dir`
4. `feat/small-roadmap-items`
5. `feat/branding`
6. `feat/layout-modes`
7. `feat/redfox-rollback-helper` (after small-roadmap-items: they touch the same recipe file, and the helper branch already resolves that)
8. `feat/system-monitor`
9. `feat/mailspring-adwaita`

Any order works for 2–5 and for 8–9.

---

## 1. smooth-overview: `harden` (merged)

- **What it does:** works on GNOME 49/50, can be turned off and on again safely, and keeps the overview's search centred when the dock is on the side.
- **Compare:** https://github.com/snakeeyes021/smooth-overview/compare/main...harden
- **Commits:** 2.
- **Look at:** `extension.js`.
- **Screenshot:** `overview-centred.png`.
- **Merged:** Matt said yes on 2026-11-03. smooth-overview's `main` is fast-forwarded to `harden` (6c91aad), and RedFox's next image build uses it.

## 2. `fix/docker-group-after-rebase` (merged)

- **What it fixes:** a machine that rebases onto RedFoxOS (from Bazzite or Bluefin) never gets a `docker` group, so Docker's socket fails to start. It now gets one.
- **Merged** 2026-11-03 (c9b5386); the `unstable` build passed.
- **Compare:** https://github.com/snakeeyes021/redfox-os/compare/unstable...fix/docker-group-after-rebase
- **Commits:** 1, 2 files.
- **Look at:** `files/system/usr/lib/sysusers.d/redfox-docker.conf`, `files/system/usr/bin/bluefin-dx-groups`.

## 3. `feat/midikeep-data-dir` (merged)

- **What it does:** Midikeep reads `data_dir` from `config.yaml` to decide where the MIDI archive goes, matching Pianola. It adds 8 tests, and all 27 tests pass.
- **Merged** 2026-11-03 (d6d61a3); the `unstable` build passed.
- **Compare:** https://github.com/snakeeyes021/redfox-os/compare/unstable...feat/midikeep-data-dir
- **Commits:** 1.
- **Look at:** `files/system/usr/bin/midikeep-daemon`, `files/system/usr/bin/midikeep`, `docs/midikeep.md`, `tests/test_midikeep.py`.

## 4. `feat/small-roadmap-items` (merged)

- **What it does:**
  - VS Code and its forks get the Antigravity, Dewy and Sloppy extensions.
  - Winboat leaves the compatibility bundle. (Matt then decided against Winboat entirely; see `fix/remove-winboat` below.)
  - Signal and Joplin start in the tray at login.
  - Claude Code defaults to its auto theme.
  - New Signal installs keep their database key in the login keyring, which removes Signal's warning dialog at first start.
- **Decided:** Matt said yes to keeping new Signal profiles in the GNOME login keyring (2026-11-03).
- **Merged** 2026-11-03 (7349ca2). Matt's caveats became the follow-up branch `fix/remove-winboat` (below) and a Hub roadmap item for per-app "start in tray at login" toggles.
- **Compare:** https://github.com/snakeeyes021/redfox-os/compare/unstable...feat/small-roadmap-items
- **Commits:** 5.
- **Look at:**
  - `files/system/usr/share/redfox/user-setup.hooks.d/55-signal-keyring.sh`
  - `files/system/usr/libexec/redfox-joplin-launch`
  - `files/system/usr/share/redfox/user-setup.hooks.d/90-vscode.sh`
  - the `configure-autostart-tray` recipe in `60-custom.just`
- **Screenshot:** `boot-tray-v2.png`.

## 5. `feat/branding` (merged)

- **What it does:**
  - RedFoxOS everywhere a person sees the OS name: About, GRUB, the login screen, the boot splash, the terminal welcome message, fastfetch and the Starship prompt.
  - The drawn nine-tailed fox for fastfetch, and the swirl symbolic icon.
  - The system still identifies itself as `bazzite` (`ID=bazzite`) on purpose; `docs/branding.md` explains why.
- **Merged** 2026-11-03 (224c464), approved as it is. The os-release `ID` change is its own follow-up, `feat/redfox-os-identity` (below).
- **Compare:** https://github.com/snakeeyes021/redfox-os/compare/unstable...feat/branding
- **Commits:** 8.
- **Look at:** `docs/branding.md`, `files/scripts/branding.sh`, `assets/branding/make-marks.py`, `files/system/usr/share/ublue-os/bazzite/fastfetch.jsonc`.
- **Screenshots:**
  - `brand-about-light.png`, `brand-about-dark.png`
  - `brand-grub.png`, `brand-gdm.png`, `brand-plymouth.png`, `brand-motd.png`
  - `brand-fastfetch-fox-v3.png`, `brand-start-button-v3.png`

## 6. `feat/layout-modes` (merged)

- **What it does:**
  - Six desktop layouts that switch live with `redfox-layout set <id>` or the `preset-dock-*` recipes, with no logout.
  - Matt's names and order: RedFox, GNOME, Ubuntu, then Cal, Wash and Nostalgia. They're applied to the `redfox-layout` ids and the `preset-dock-*` recipes too (`preset-dock-cal`, `preset-dock-wash`, `preset-dock-nostalgia`), with no aliases for the old names.
  - Wash and Nostalgia have:
    - a blurred taskbar;
    - the swirl start button and the tiling button side by side;
    - the clock after the status icons.
  - The Ubuntu layout's top bar and dock now match in the overview.
  - SVG previews for RedFox Hub's layout picker, with a light border round each picture, and `assets/layouts/picker.html`, a mock-up of the picker with a hover lift.
  - The VM testbed in `tests/vm/`.
- **Merged** 2026-11-03 (ed79263). It builds smooth-overview from its `main`, which has `harden`.
- **Compare:** https://github.com/snakeeyes021/redfox-os/compare/unstable...feat/layout-modes
- **Commits:** 17.
- **Look at:**
  - `files/system/usr/bin/redfox-layout`
  - `files/system/usr/share/gnome-shell/extensions/redfox-layouts@redfoxlabs.tech/extension.js`
  - `docs/layout-names.md`
  - `tests/vm/README.md`
- **Screenshots:**
  - `layout-names-v2.png`, and the picker mock-up at `layout-picker/` (hover a card);
  - `layout-redfox.png`, `layout-ubuntu.png`, `layout-ubuntu-overview.png`, `layout-cal.png`, `layout-wash.png`, `layout-nostalgia.png`.

  VM-tested after the rename (2026-11-03): all six `preset-dock-*` recipes switch live, the old recipe names and ids are gone, and there are no shell errors.
- **Ubuntu dock line, fixed:** the thin line between the dock and the top bar (and down the dock's sides) was a 1 px border from Blur my Shell's dark dock style (`.dark-dash` in its `stylesheet.css`). The helper extension's new `stylesheet.css` removes it on full-height docks only; floating docks keep it as their outline. Checked on the desktop, in the overview, on hover and after switching layouts. Shots: `ubuntu-dock-corner-before-after.png`.
- **Needs:** smooth-overview `harden`.

## 7. `feat/redfox-rollback-helper` (merged)

- **What it does:** `redfox-rollback-helper` lists RedFoxOS builds by commit and date, and rolls back or moves to one. `ujust rollback-helper` (and `bruh`) open it.
- **Merged** 2026-11-03 (8da831c).
- **Compare:** https://github.com/snakeeyes021/redfox-os/compare/unstable...feat/redfox-rollback-helper
- **Commits:** 1.
- **Look at:** `files/system/usr/bin/redfox-rollback-helper`.
- **Merge after:** `feat/small-roadmap-items`.

## 8. `feat/system-monitor` (merged)

- **What it does:**
  - New installs get Resources instead of Mission Center, and Dewy's dock pins it.
  - Ctrl+Shift+Esc, Ctrl+Alt+Del on the keypad and Logo Menu's button open it. Where only Mission Center is installed, they open that.
  - Existing installs keep Mission Center.
  - The measurements behind the choice are in `docs/system-monitor.md`.
- **Decided:** Matt said yes to Resources (2026-11-03).
- **Merged** 2026-11-03 (49c6e6f).
- **Compare:** https://github.com/snakeeyes021/redfox-os/compare/unstable...feat/system-monitor
- **Commits:** 2.
- **Look at:** `docs/system-monitor.md`, `files/system/usr/bin/redfox-system-monitor`, the `redfox.d` dconf additions, `recipes/_common-modules.yml`.
- **Screenshot:** `system-monitor-resources.png`.

## 9. `feat/mailspring-adwaita` (merged)

- **Merged** 2026-11-03, approved by Matt at v6.1 ("that looks good, yup, thanks for cleaning it up").
- **What ships:**
  - RedFox Adwaita Light and Dark, Mailspring themes written from scratch. Mailspring's Automatic theme uses them, so it follows GNOME's light/dark setting and accent colour. A light or dark theme the user picked is kept.
  - GNOME's Adwaita symbolic icons in place of Mailspring's, loaded from the system's icon theme (nothing copied).
  - A small companion plugin (`redfox-gnome-integration`): the window buttons follow GNOME's button layout live; Reply / Reply all / Forward in the header bar; the icon lookup.
  - The contact panel starts hidden; the header's sidebar button brings it back, and a choice the user made is kept.
  - Installed per user by the login hook `70-mailspring-theme.sh`. No per-user font copy: fonts come from the system-wide Flatpak font fix (13).
- **Known limits** (Mailspring is Electron, so a theme can't change these):
  - no GNOME split header bar, and row heights stay Mailspring's;
  - no native rounded window corners, menus or dialogs;
  - Mailspring puts the plugin's Reply group after its own header buttons;
  - no avatars or thread-list header yet; the unread dot and attachment file-type icons stay Mailspring's.
  - The plugin uses Mailspring's internal plugin APIs, so each Mailspring update needs a quick check (buttons in place, Reply opens a draft). If it breaks, Mailspring logs an error and the theme still works.
- **Iterations:** v1 to v6.1 side by side with vanilla Mailspring and a GTK 4 mock: https://redmax.taila6a47f.ts.net:8401/mailspring-compare/
- **Look at:** `docs/mailspring-adwaita.md`, `files/system/usr/share/redfox/mailspring/`, `files/system/usr/share/redfox/user-setup.hooks.d/70-mailspring-theme.sh`, `tools/mailspring-mock/`.


## 10. `fix/remove-winboat` (follow-up to 4, merged)

- **What it does:**
  - Removes Winboat completely, as Matt asked ("we don't want winboat at all. No ujust."): the `install-winboat` and `uninstall-winboat` recipes, the roadmap items, and FreeRDP, which was in the image only for Winboat.
  - Makes Signal's and Joplin's tray entries safe after an uninstall. `configure-autostart-tray` already skipped apps that weren't installed, but an app removed later left its login entry, and Joplin's app-grid override, behind. Each entry now has `TryExec` pointing at the Flatpak's launcher, so GNOME skips it once the app is gone.
- **Merged** 2026-11-03 (112c05f), FreeRDP included, as Matt approved.
- **Compare:** https://github.com/snakeeyes021/redfox-os/compare/unstable...fix/remove-winboat
- **Commits:** 1.
- **Look at:** the `configure-autostart-tray` recipe in `60-custom.just`, `recipes/_common-modules.yml`.
- **Tested in the VM:**
  - The entries get `TryExec`, and both login services are generated.
  - An entry whose app is missing gets no login service and is hidden from the app grid.
  - Joplin's own entry still loads.


## 11. `feat/redfox-os-identity` (merged)

- **Merged** 2026-11-03, approved by Matt. He keeps `uupd` (automatic background updates, applied on restart) alongside topgrade (update now).
- **What it does:** os-release says `ID=redfox` with `ID_LIKE="bazzite fedora"` (`files/scripts/branding.sh`).
- **Audit of the built image:**
  - No systemd unit has an os-release condition.
  - Bazzite's 16 scripts, services and ujust recipes read `image-info.json`, not `ID`.
  - The `ID` readers (`grub2-mkconfig`, `distrobox-generate-entry`, the bash prompt, `lsb_release`) only display it, or check a path that doesn't match either way.
  - topgrade falls back to `ID_LIKE` and keeps running `rpm-ostree upgrade`.
  - Starship reports Fedora, which RedFox's prompt draws as the fox.
  - Nothing needed patching.
- **Tested in VMs:**
  - an existing RedFoxOS install updating onto it, and rolling back to `ID=bazzite` and forward;
  - Bazzite → RedFoxOS;
  - Bluefin → RedFoxOS.

  All three boot, run Bazzite's services, keep the docker group, and answer topgrade, `uupd` and `bootc upgrade --check`.
- **Found:** a stale greenboot record from an earlier RedFoxOS → Bluefin rebase made RedFoxOS roll the Bluefin VM back after its first boot. A clean Bluefin machine stays on RedFoxOS. Written up in `tests/vm/README.md` with the one-line fix.
- **Compare:** https://github.com/snakeeyes021/redfox-os/compare/unstable...feat/redfox-os-identity
- **Look at:** `files/scripts/branding.sh`, `docs/branding.md`, `tests/vm/README.md`.

## 12. `chore/wallpaper-credits` (merged)

- **What it does:** credits both default wallpapers to Paweł Czerwiński (Unsplash License).
  - The light one is the top 16:9 crop of "Pastel ink clouds in water".
  - The dark one is "Pink and blue abstract painting".
  - Both were matched pixel for pixel against his Unsplash photos.
  - Adds `docs/wallpaper-credits.md` with links, the licence's limits, and three candidate light/dark pairs; a `CREDITS` file next to the images; and `<author>`/`<license>` in the GNOME wallpaper entry, as Fedora's wallpapers have. Rewords the roadmap item for collecting more pairs.
- **Merged** 2026-11-03, approved by Matt.
- **Compare:** https://github.com/snakeeyes021/redfox-os/compare/unstable...chore/wallpaper-credits
- **Commits:** 1.
- **Look at:** `docs/wallpaper-credits.md`.


## 13. `fix/flatpak-system-fonts` (merged)

- **Merged** 2026-11-03 (fda4456), approved by Matt; its unstable build (run 41711731534) passed on all three variants.
- **What it fixes:** Flatpak apps on the Freedesktop 26.08 runtime (OBS, Mailspring, …) couldn't see any system fonts and fell back to DejaVu Sans. Upstream: [freedesktop-sdk#1563](https://gitlab.com/freedesktop-sdk/freedesktop-sdk/-/issues/1563).
- **How:** a boot-time oneshot (`redfox-flatpak-fonts.service`) puts a small fontconfig file in `/var/lib/redfox/flatpak-fonts` and adds one system-wide Flatpak override: read access to that folder, and `FONTCONFIG_FILE` pointing at it. Bazzite's own override entries are kept. `redfox-flatpak-fonts remove` undoes exactly what it added, for when the runtime is fixed.
- **Tested in the VM:**
  - OBS and Mailspring go from 0 host fonts to 277 and use Adwaita Sans;
  - it survives reboots and applies from a clean state at boot;
  - `remove` restores the override file exactly;
  - it's harmless on 25.08 and GNOME-runtime apps.

  Screenshot: `flatpak-fonts-mailspring.png` (Mailspring in Adwaita Sans with no per-user font copy).
- **Once merged:** the Mailspring branch's per-user copy of Adwaita Sans becomes unnecessary and can be dropped.
- **Compare:** https://github.com/snakeeyes021/redfox-os/compare/unstable...fix/flatpak-system-fonts
- **Look at:** `docs/flatpak-fonts.md`, `files/system/usr/libexec/redfox-flatpak-fonts`, `files/system/usr/share/redfox/flatpak-fonts/fonts.conf`.

## 14. `fix/greenboot-stale-record` (merged)

- **Merged** 2026-11-03 (825a4d7), pre-approved by Matt.
- **What it fixes:** the rollback trap found under 11. `redfox-greenboot-stale-check.service` runs just before greenboot's health check. It clears greenboot's record only when the default deployment booted and the record names another one, which can only be left over from an earlier rebase. A genuine fallback boots a non-default deployment, so greenboot still rolls back.
- **Tested in VMs:** RedFoxOS → Bluefin → RedFoxOS stays on RedFoxOS; a normal update; an update whose health check always fails still rolls back; a GRUB-fallback state is left to greenboot. Details in `tests/vm/README.md`.

## 15. `fix/update-lock-wait` (ready for review)

- **What it fixes:** uupd (the automatic update) and topgrade (`ujust update`) both use rpm-ostree/bootc, and the second one to start failed with "System transaction in progress" instead of waiting. uupd's timer is `Persistent=true`, so it often runs right after boot, just when someone might run `ujust update`.
- **How:** `/usr/libexec/redfox-wait-for-system-update` waits (up to an hour, then carries on) while uupd, a `bootc upgrade/switch/rollback` or an rpm-ostree transaction is running. topgrade runs it as a pre-command; uupd runs it as `ExecStartPre` through a drop-in.
- **Tested in the VM, both orders:**
  - `ujust update`'s topgrade during uupd's `bootc upgrade`: it printed "Waiting for the automatic update to finish first...", then the system update was OK. Before the fix it failed at once.
  - uupd started during topgrade's `rpm-ostree upgrade`: it waited 2 minutes, then ran cleanly with no restarts. Before, it failed and relied on systemd's retry (3 tries in 10 minutes).
- **Compare:** https://github.com/snakeeyes021/redfox-os/compare/unstable...fix/update-lock-wait
- **Look at:** `files/system/usr/libexec/redfox-wait-for-system-update`, `files/system/usr/lib/systemd/system/uupd.service.d/50-redfox-wait.conf`, `files/system/usr/share/ublue-os/topgrade.toml`.

## 16. `feat/redfox-hub` (ready for review)

- **What it is:** RedFox Hub (`tech.redfoxlabs.Hub`), built into the image, with the five sections Matt chose: Welcome, Apps, Updates, Settings and Manual. Design: `docs/redfox-apps-design.md`, with each rule marked as Matt's decision or a proposal.
- **Preview** (real screenshots from a built image, light and dark, with the questions): https://redmax.taila6a47f.ts.net:8413/
- **What's in it:**
  - Welcome: a five-page tour in GNOME Tour's manner, shown once per user at first login, after Bazzite Portal closes.
  - Updates: the RedFox updater (Matt, 11-04). Status, update now with its output, automatic updates on/off, restart, the channel, go back, and other builds.
  - Apps: RedFox's packs from one catalog, `/usr/share/redfox/software.yaml`, read by the new `redfox-software`; every `install-*` recipe now calls it.
  - Settings: the layout picker; Extra Dimming (21); "start in the tray at login" switches (`redfox-autostart`); the MIDI archive folder (`midikeep data-dir`).
  - Manual: seven pages, no `ujust`.
  - The old RedFox Updater launcher opens Hub › Updates and is hidden from the app grid; the terminal tips point at Hub.
- **Tested** on an image built from the branch, in the VM: the first-login Welcome shows once; update now ran topgrade to the end; going back and forth; the password prompts for automatic updates and for switching channel, and cancelling them; a layout switch from Hub; installing an app from Apps. 53 unit tests pass (`tests/test_hub_*.py`, `tests/test_redfox_software.py`, `tests/test_midikeep.py`).
- **Compare:** https://github.com/snakeeyes021/redfox-os/compare/unstable...feat/redfox-hub
- **Look at:** `files/hub/` (the app, a meson project), `files/system/usr/bin/redfox-updates`, `redfox-autostart`, `redfox-software`, `files/system/usr/share/redfox/software.yaml`, `files/scripts/install-redfox-hub.sh`.
- **Questions for Matt:** on the preview page. In short: Welcome's words; hiding the old updater launcher; renamed packs; dropping the automatic tray step from `configure-matt`; keeping Bazzite Portal; existing users seeing the tour once; the two `ujust` lines in the terminal banner.

## 17. First 15 minutes on a fresh install (merged fixes)

Walked on a fresh `:unstable` install; findings in `docs/first-15-minutes.md`, screenshots in `/var/home/matt/previews/first-15/`. Four clear bug fixes were merged, each tested in the VM:
- `fix/libvirt-secrets-dir` (fc43ec4): libvirt never started on a fresh install.
- `fix/topgrade-missing-include` (75e106f): every `ujust update` began with an error about a missing `/etc/ublue-os/topgrade.toml` on the Fedora 45 base.
- `fix/motd-layout-tip` (98e7103): a terminal tip used the old layout names.
- `fix/motd-swedish-template` (87c211f): Swedish users got Bazzite's terminal banner.

The rest (Steam autostart, Portal, announcements, the dock, the default layout, wallpapers, and more) is listed in the doc for Matt.

## 18. RedFox Dim review fixes (merged)

- **What it fixes:** the three findings of the RedFox Dim review: a failed `enable()` is now undone instead of leaving the brightness hooks installed; changing `darkest-level` updates direct scanout for fallback-dimmed monitors; Zoom no longer covers the dim.
- **Merged** 2026-11-07 (0d47f5e); the `unstable` build passed. Tested in the VM on GNOME 51.1 with the fallback slider: zoom while dimmed, `darkest-level` 1.0 and back, and an `enable()` made to fail. Dewy has an FYI on Trello.

## 19. Feature branch images in CI (merged)

- **What it does:** a `feature/…` branch gets its own test images (`br-<branch>-<fedora>`, `fb-<branch>-<sha7>-<fedora>`), listed in Hub's image picker. Each build deletes the branch's older images, and deleting the branch deletes them all. See `docs/ci.md`.
- **Merged** 2026-11-07 (c39d014), after five builds of a throwaway `feature/ci-smoke` branch. They found and fixed three bugs in the cleanup. The workflow's own token can delete GHCR versions, so no setting needs changing.
- **Note:** the delete-on-branch-deletion workflow only runs from `main`, so it takes effect at the next promotion. Until then, a deleted `feature/…` branch leaves its last images behind.
- The old `feature/midikeep`, `feature/redfox-nord` and `feature/topgrade-updater` images were deleted from GHCR (all three branches merged or gone).

## 20. One graphics rule set: `feat/gpu-detect` (merged) and `feat/gpu-rules`

- **What it does:** `files/system/usr/share/redfox/gpu-rules.json` says which image suits which display devices (NVIDIA from 0x1e00 on → NVIDIA, older NVIDIA → legacy, Intel/AMD alone → mainline, hybrid laptops marked). The download page and Hub's "(Recommended)" both apply it; `tests/gpu-cases.json` holds the ten machines both are tested against.
- `extras/identify_gpu.sh` now prints a code to paste into the download page (`RFX1 8086:46a6 10de:1c03`), and `extras/identify_gpu.ps1` does the same on Windows.
- **Merged:** `feat/gpu-detect` (rules, cases, both detectors, README tip) on 2026-11-07.
- **Waiting:** `feat/gpu-rules` switches Hub's `redfox-rollback-helper` to the shared file. It sits on `feat/image-picker`, so it merges with that.

## 21. Hub: an Extra Dimming switch (in `feat/redfox-hub`)

Matt, 11-07: RedFoxOS's own shell extensions get a switch in Hub. Settings › Desktop › **Extra Dimming** turns RedFox Dim on and off (`gnome-extensions enable|disable`), and hides itself without the extension. Tested in the VM. It's merged into `feat/redfox-hub` (e30c00b), so it lands with Hub (16).

---

## Also waiting for Matt (not branches)

- RedFox Hub: see 16 (and 21).
- The first-15-minutes findings for Matt: see 17.
- Not building a GNOME front end for Mailspring (`docs/mailspring-gnome-frontend.md`): agree or not.

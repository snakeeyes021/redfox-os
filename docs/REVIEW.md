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

## 9. `feat/mailspring-adwaita` (on hold)

- **What it does:**
  - RedFox's own Adwaita themes for Mailspring, light and dark, written from scratch.
  - A login hook installs them and makes them Mailspring's automatic themes, so Mailspring follows GNOME's light/dark setting and accent colour.
  - A themed light or dark choice you've already made in Mailspring is kept.
- **On hold:** Matt says it "doesn't look very adwaita". A side-by-side comparison with a real libadwaita app is being prepared.
- **Compare:** https://github.com/snakeeyes021/redfox-os/compare/unstable...feat/mailspring-adwaita
- **Commits:** 2.
- **Look at:**
  - `files/system/usr/share/redfox/mailspring/adwaita.less`
  - `files/system/usr/share/redfox/mailspring/adwaita-variables.less`
  - `files/system/usr/share/redfox/user-setup.hooks.d/70-mailspring-theme.sh`
- **Screenshots:** `mailspring-adwaita-light.png`, `mailspring-adwaita-dark.png`.


## 10. `fix/remove-winboat` (follow-up to 4)

- **What it does:**
  - Removes Winboat completely, as Matt asked ("we don't want winboat at all. No ujust."): the `install-winboat` and `uninstall-winboat` recipes, the roadmap items, and FreeRDP, which was in the image only for Winboat.
  - Makes Signal's and Joplin's tray entries safe after an uninstall. `configure-autostart-tray` already skipped apps that weren't installed, but an app removed later left its login entry, and Joplin's app-grid override, behind. Each entry now has `TryExec` pointing at the Flatpak's launcher, so GNOME skips it once the app is gone.
- **Compare:** https://github.com/snakeeyes021/redfox-os/compare/unstable...fix/remove-winboat
- **Commits:** 1.
- **Look at:** the `configure-autostart-tray` recipe in `60-custom.just`, `recipes/_common-modules.yml`.
- **Tested in the VM:**
  - The entries get `TryExec`, and both login services are generated.
  - An entry whose app is missing gets no login service and is hidden from the app grid.
  - Joplin's own entry still loads.
- **Check:** whether to keep FreeRDP for other remote-desktop uses. It's one line to put back.


## 11. `feat/redfox-os-identity` (follow-up to 5, in progress)

- **Plan:** os-release `ID=redfox` and `ID_LIKE="bazzite fedora"`. Audit every script and unit in the image that reads `ID` or `image-info.json`, and patch or retire each one. Tested in the VM from a fresh first boot and from a rebase.
- **Findings so far, from the running image:**
  - Bazzite's scripts, services and ujust recipes read `image-info.json` (image name and base image), not `ID`.
  - The `ID` readers are cosmetic (`lsb_release`, the shell prompt) or no-ops (`grub2-mkconfig`'s EFI-path check).
  - topgrade falls back to `ID_LIKE`, so it keeps running `rpm-ostree upgrade`.

---

## Also waiting for Matt (not branches)

- RedFox Hub (`docs/redfox-apps-design.md`): Welcome's words and pages. (Decided 2026-11-03: rebuild GNOME Tour's look in Python/libadwaita, don't fork it.)
- Not building a GNOME front end for Mailspring (`docs/mailspring-gnome-frontend.md`): agree or not.

# RedFoxOS branding

What RedFoxOS changes so that it calls itself RedFoxOS rather than Bazzite, what it deliberately leaves alone, and the artwork still wanted.

The name is **RedFoxOS** (as in the README and the wordmark); the short name is `redfox`.

## Names people see

| Where | How | Notes |
| --- | --- | --- |
| `/usr/lib/os-release` (`NAME`, `PRETTY_NAME`, `LOGO`, URLs, `DEFAULT_HOSTNAME`, `BOOTLOADER_NAME`, `IMAGE_ID`, `ANSI_COLOR`) | `files/scripts/branding.sh` | Feeds Settings → About, `hostnamectl`, fastfetch's OS line, and the boot menu. |
| Boot menu (GRUB) entries | `PRETTY_NAME` | ostree writes "RedFoxOS (ostree:0)" when it creates a deployment, so the old entries keep their old titles until they are replaced. |
| Settings → About logo | `LOGO=redfox-logo`, icons in `/usr/share/icons/hicolor` | About looks for `redfox-logo-text-dark` (dark mode), `redfox-logo-text`, then `redfox-logo`. |
| Default hostname | `/etc/hostname` and `DEFAULT_HOSTNAME` = `redfox` | Only applies where no hostname has been set. |
| Login screen (GDM) | `/usr/share/pixmaps/fedora-gdm-logo.png` | Light lettering, since GDM's background is dark. |
| Boot splash (Plymouth) | `/usr/share/plymouth/themes/spinner/watermark.png`, and `branding.sh` rebuilds the initramfs | The initramfs carries its own copy of the theme. Before this, RedFox's watermark was in `/usr` but the boot screen still showed Bazzite's. |
| Terminal banner (MOTD) | `/usr/share/ublue-os/motd/template.md`, `tips/20-redfox.md` | Bazzite's tips (gaming, Bazzite docs links) are removed at build. |
| fastfetch | `/usr/share/ublue-os/bazzite/fastfetch.jsonc`, `logo.txt`, `/usr/libexec/bazzite-fetch-image` | A sitting nine-tailed fox in RedFox reds, drawn for the terminal (truecolour half blocks, 38×22 so it fits a default 80×24 terminal; see Artwork). The image line shows the image actually booted, e.g. `ghcr.io/snakeeyes021/redfox-os:unstable`. Keys still follow the GNOME accent colour. |
| Symbolic icon | `/usr/share/icons/hicolor/scalable/apps/redfox-logo-symbolic.svg` | The swirl: three swirling tails with fox ears, one colour. ArcMenu's start button in the Windows layouts, and anything that asks for `redfox-logo-symbolic`. |
| Starship | `/usr/share/redfox/starship.toml`, used when you have no `~/.config/starship.toml` | Turns on the `os` module with a 🦊. Starship isn't installed by default yet (see the roadmap). |
| Fedora's logo files (`fedora-logo*.png`, `fedora_whitelogo*`, `system-logo-white.png`) | `files/system/usr/share/pixmaps` | Shown by the installer, initial setup and some About dialogs. |

### Left as Bazzite on purpose

- **Bazzite Portal** (the first-run app, `yafti`) and **Bazzite Announcements**. Their content is Bazzite's own (Bazzite docs, Discord, Bazzite actions and news), so renaming them would mislead. The RedFox Welcome app is meant to replace the Portal (see `docs/redfox-apps-design.md`).
- **`ujust` recipe names.**

## Identifiers tooling reads (kept)

| Identifier | Kept as | Who reads it |
| --- | --- | --- |
| os-release `ID` | `bazzite` | Starship and other `os_info` users (an unknown ID makes them guess Fedora); Bazzite's and Universal Blue's scripts. `ID=redfox` with `ID_LIKE="bazzite fedora"` would be the textbook way to mark a derivative, but nothing a person sees reads `ID`, and keeping it avoids breaking anything that checks for Bazzite. |
| `ID_LIKE`, `VERSION`, `VERSION_ID`, `VERSION_CODENAME`, `VARIANT`, `VARIANT_ID`, `CPE_NAME`, `BUILD_ID`, `OSTREE_VERSION`, `SUPPORT_END` | Bazzite's values | Version and support tracking; RedFox follows Bazzite's Fedora version and support window. |
| `image-info.json` `base-image-name`, `fedora-version`, `version`, `image-tag`, `image-branch` | Bazzite's values | Bazzite's hardware setup, user setup and Flatpak manager compare these to decide whether to run again; `base-image-name` (`silverblue`) picks GNOME-specific behaviour. |

### Changed in `image-info.json`

`image-name` (now `redfox-os`, `redfox-os-nvidia` or `redfox-os-nvidia-legacy`), `image-vendor` (`snakeeyes021`) and `image-ref` (`ghcr.io/snakeeyes021/<image>`). Bazzite's scripts only check `image-name` for the substrings `nvidia`, `deck` and `dx`, which RedFox's names contain or lack exactly as the Bazzite images they're built on do. Changing it makes Bazzite's hardware setup and Flatpak manager run once more after the update that brings this change (both are safe to repeat). The MOTD shows `image-ref`.

### Rollback helper

Bazzite's `bazzite-rollback-helper` (also run by `bruh`) only knows Bazzite's images (`ghcr.io/ublue-os/bazzite-*`), so its `list` and `rebase` offered Bazzite. `feat/redfox-rollback-helper` adds `redfox-rollback-helper` (`ujust rollback-helper`) for RedFox's images and points `bazzite-rollback-helper` at it.

## Artwork

Two marks are drawn in code by `assets/branding/make-marks.py` (with `brush.py`), because the painting can't be shrunk that far:

- **The terminal fox** (`assets/branding/terminal-fox.png`): a simplified version of the painted fox, sitting and turned toward the viewer, with nine tails curling at the tips. The terminal version places the eyes and nose pixel by pixel so they stay crisp. It needs a terminal with 24-bit colour (Ptyxis and other modern terminals); a bare text console shows it in approximate colours.
- **The swirl** (`assets/branding/swirl.png`): the symbolic mark for small, one-colour places. Fox heads drawn as geometric faces are common in logos; the swirling tails are what's RedFox's own.

Everything else is made from the existing art by `assets/branding/make-images.py`: the nine-tailed fox (`assets/red_fox_labs_logo_2_semi-transparent.png`, white-filled so it reads on light and dark) and the "RedFoxOS" wordmark (`assets/branding/wordmark-source.png`, cut from `updatelogo.png`). For dark backgrounds the lettering is recoloured light; no new marks are drawn. Rerun the script after changing the source art.

### Wanted from Matt (new artwork)

These need art that doesn't exist yet. The plan is to commission a human artist to paint the watercolour fox properly; the same job should redraw the terminal fox and the swirl, and set the wordmark as a vector.

1. **The fox as a vector (SVG).** Every RedFox icon is currently scaled from a ~960 px painting, so it's soft on HiDPI and smudgy at 16–32 px (app grid, window list, About at 2×).
2. **A finished version of the swirl (SVG)**, legible at 16 px and as a symbolic icon. The drawn stand-in is on ArcMenu's start button; it could also go on the Logo Menu and replace the painted fox in 16–32 px icons, where the painting doesn't survive.
3. **The wordmark as a vector**, or the name of its font, so the lettering can be set at any size and colour. The largest copy today is about 700×170 px.
4. *(Optional)* **A light-on-dark version of the full lockup** drawn on purpose, if the recoloured lettering isn't right.

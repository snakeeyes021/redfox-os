# RedFox Hub

RedFoxOS's own app: Welcome, Apps, Updates, Settings and Manual. Python, GTK 4 and libadwaita; the design is in [`docs/redfox-apps-design.md`](../../docs/redfox-apps-design.md).

It's a meson project that installs to any prefix:

```sh
meson setup build --prefix=/usr
meson install -C build
```

The RedFoxOS image builds it this way, into `/usr` (`files/scripts/install-redfox-hub.sh`). It lives under `files/` because BlueBuild only gives build scripts that folder.

To try it from the source tree without installing: `python3 -c 'import sys; sys.path.insert(0, "src"); from redfox_hub.app import main; main()'`.

## Layout

- `src/redfox_hub/`: one module per section (`welcome`, `apps`, `updates`, `settings`, `manual`), the window, `host.py` and `paths.py`.
- `data/`: `style.css`, the layout previews (`layouts/`, drawn by `assets/layouts/make-previews.py`), the Manual pages (`manual/`, format in the design doc), the desktop entry, metainfo and icons.

## Packaging

Hub doesn't care where it's installed. The two places that would change for a Flatpak:

- **Host commands** all go through `host.host_argv()`. Installed on the host, Hub runs them directly; in a Flatpak (`/.flatpak-info` exists), through `flatpak-spawn --host`. Nothing else in the app reaches the host.
- **The welcome marker** is `~/.local/state/redfox/welcome-seen` on the host (`paths.host_state_dir()`), shared with the first-login script in the image.

A Flatpak manifest would need `--talk-name=org.freedesktop.Flatpak` (for `flatpak-spawn --host`), `--filesystem=~/.local/state/redfox:create`, and `--filesystem=/var/lib/flatpak/exports/share/icons:ro` plus `--filesystem=xdg-data/flatpak/exports/share/icons:ro` so app icons show in Apps. Folder choosing and the clipboard go through portals already.

The commands Hub calls are part of the image, not of Hub: `redfox-updates`, `redfox-autostart`, `redfox-layout`, `redfox-software`, `redfox-rollback-helper`, `midikeep`, `gsettings`, `flatpak` and `systemctl`.

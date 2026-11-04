# RedFox Hub

RedFoxOS's own app: Welcome, Apps, Updates, Settings and Manual. Python, GTK 4 and libadwaita; the design is in [`docs/redfox-apps-design.md`](../../docs/redfox-apps-design.md).

It's a meson project:

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

Hub is part of the image, not a Flatpak (Matt, 11-04: "It is specific to the OS and wouldn't be helpful to others on a different OS"). It runs the image's commands directly: `redfox-updates`, `redfox-autostart`, `redfox-layout`, `redfox-software`, `redfox-rollback-helper`, `midikeep`, `gsettings`, `flatpak` and `systemctl`. Those commands belong to the image, not to Hub, and work the same in a terminal.

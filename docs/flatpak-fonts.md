# Flatpak apps and the system's fonts

**Symptom:** Flatpak apps on the Freedesktop 26.08 runtime can't see any of the system's fonts: OBS, Mailspring, and any other app on that runtime. They fall back to DejaVu Sans, so Adwaita Sans, Adwaita Mono and anything installed system-wide never show. Apps on the 25.08 runtime and GNOME apps were fine when checked.

**Cause:**
- Flatpak shows an app the host's fonts at `/run/host/fonts`, and tells fontconfig to treat that folder as `/usr/share/fonts`, the runtime's own font folder.
- Fontconfig names and checks its caches by folder path and timestamp. On an image-based system (ostree), every folder under `/usr` has timestamp 0, on the host and in the runtime alike.
- So fontconfig can't tell the two folders apart. It reuses the runtime's cached listing, and never scans the host's font folders.

Upstream: [freedesktop-sdk#1563](https://gitlab.com/freedesktop-sdk/freedesktop-sdk/-/issues/1563). Clearing an app's font cache doesn't help: it's rebuilt the same way.

**RedFoxOS's fix (`fix/flatpak-system-fonts`):**
- `/usr/share/redfox/flatpak-fonts/fonts.conf` loads the runtime's normal fontconfig setup, then gives `/run/host/fonts` its own name again, with its own cache folder (`fontconfig-redfox`).
- `redfox-flatpak-fonts.service` (a boot-time oneshot) runs `/usr/libexec/redfox-flatpak-fonts apply`. That copies the file to `/var/lib/redfox/flatpak-fonts/`, where apps can be given read access (not `/usr` or `/etc`). It then adds one system-wide Flatpak override, in `/var/lib/flatpak/overrides/global`:
  - `--filesystem=/var/lib/redfox/flatpak-fonts:ro`
  - `--env=FONTCONFIG_FILE=/var/lib/redfox/flatpak-fonts/fonts.conf`

  Bazzite's own entries in that file are left alone.
- Tested in the VM with OBS and Mailspring (26.08 runtime): both go from 0 host fonts to all 277, and use Adwaita Sans. It's harmless on apps that already worked: Brave and Spotify (25.08) and GNOME Text Editor (GNOME 51) all still see the host fonts, with emoji intact.

**One trade-off:** an app that sets its own `FONTCONFIG_FILE` would have it replaced. None of the installed apps do.

## Removing it once the runtime is fixed

1. Check that a 26.08 app sees host fonts without the fix. Run:

       flatpak run --env=FONTCONFIG_FILE= --command=fc-match com.obsproject.Studio "Adwaita Sans"

   It should print Adwaita Sans.
2. For one release, change the service's `ExecStart` to `redfox-flatpak-fonts remove`. That takes out only RedFox's two override entries and the copied file.
3. Then delete the service, `/usr/libexec/redfox-flatpak-fonts`, `/usr/share/redfox/flatpak-fonts/`, the recipe line that enables the service, and this page.

By hand, at any time: `sudo /usr/libexec/redfox-flatpak-fonts remove` (or `apply`, or `status`).

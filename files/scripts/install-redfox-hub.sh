#!/usr/bin/env bash
# Build and install RedFox Hub (files/hub, a meson project) into /usr.
#
# Hub is packaged so it can install to any prefix; in the image it goes to
# /usr. meson and ninja are only needed for this step, so they're removed
# again afterwards if this script installed them.
set -oue pipefail

SRC=/tmp/files/hub
BUILD=/tmp/redfox-hub-build

added=()
for pkg in meson ninja-build; do
    rpm -q "$pkg" >/dev/null 2>&1 || added+=("$pkg")
done
if [ "${#added[@]}" -gt 0 ]; then
    dnf -y install "${added[@]}"
fi

meson setup "$BUILD" "$SRC" --prefix=/usr
meson install -C "$BUILD"
rm -rf "$BUILD"

if [ "${#added[@]}" -gt 0 ]; then
    dnf -y remove "${added[@]}"
fi

# Check that it installed where the launcher looks (no display needed).
python3 -c 'import sys; sys.path.insert(0, "/usr/share/redfox-hub"); import redfox_hub.paths as p; print("redfox-hub", p.VERSION)'
gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
echo "RedFox Hub installed."

#!/usr/bin/bash
# Signal keeps the key to its message database in a file. The Flathub build
# leaves that key in plain text unless told to use the desktop's keyring, and
# warns about it in a dialog the first time Signal starts. Signal's own Linux
# build already uses the keyring on GNOME, so do the same for the Flatpak:
# the key is then encrypted by the login keyring, which unlocks at login.
#
# Only for a Signal that hasn't been set up yet. An existing profile keeps
# the store it was made with, since Signal can't read its database if the
# store changes under it. A store the user set is left alone.

set -euo pipefail

APP=org.signal.Signal
CONFIG="$HOME/.var/app/$APP/config/Signal/config.json"

command -v flatpak &> /dev/null || exit 0
[ -e "$CONFIG" ] && exit 0
flatpak override --user --show "$APP" 2>/dev/null | grep -q '^SIGNAL_PASSWORD_STORE=' && exit 0

flatpak override --user --env=SIGNAL_PASSWORD_STORE=gnome-libsecret "$APP"
echo "Signal will keep its database key in the login keyring."

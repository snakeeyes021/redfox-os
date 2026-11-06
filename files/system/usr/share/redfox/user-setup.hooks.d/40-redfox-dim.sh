#!/usr/bin/bash
# RedFox Dim is on by default, but anyone who has ever changed their extensions
# has their own list and won't see a new default. Add it to their list once, so
# that turning it off later sticks.

MARKER="${XDG_STATE_HOME:-$HOME/.local/state}/redfox/dim-enabled"
[ -e "$MARKER" ] && exit 0

python3 - <<'PY' || exit 1
from gi.repository import Gio

UUID = "redfox-dim@redfoxlabs.tech"
shell = Gio.Settings.new("org.gnome.shell")
enabled = shell.get_strv("enabled-extensions")
if UUID not in enabled:
    shell.set_strv("enabled-extensions", enabled + [UUID])
    Gio.Settings.sync()
PY

mkdir -p "$(dirname "$MARKER")"
touch "$MARKER"

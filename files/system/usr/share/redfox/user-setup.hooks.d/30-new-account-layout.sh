#!/usr/bin/bash
# New accounts start in the RedFox layout: a floating dock on big screens,
# the GNOME dash on small ones. Only accounts made on RedFoxOS have the
# marker (from /etc/skel), so an existing account's layout is left alone.
# It can be changed any time in RedFox Hub › Settings › Layout.

set -euo pipefail

MARKER="${XDG_CONFIG_HOME:-$HOME/.config}/redfox/new-account"

[ -e "$MARKER" ] || exit 0
if redfox-layout set redfox; then
    rm -f -- "$MARKER"
    echo "Started this account in the RedFox layout."
fi

#!/usr/bin/bash
# Bazzite Portal doesn't open by itself on RedFoxOS (see
# files/scripts/no-bazzite-portal-autostart.sh). An account created before
# that change has its own copy of the autostart entry: remove it once, if it's
# still the one Bazzite put there, switched on. One the user changed is left alone.

set -euo pipefail

ENTRY="$HOME/.config/autostart/bazzite-portal.desktop"
STAMP="$HOME/.local/state/redfox/bazzite-portal-autostart-removed"

[ -e "$STAMP" ] && exit 0
if [ -f "$ENTRY" ] \
    && grep -qx 'Exec=yafti_gtk.py /usr/share/yafti/yafti.yml' "$ENTRY" \
    && grep -qx 'X-GNOME-Autostart-enabled=true' "$ENTRY" \
    && [ "$(grep -c . "$ENTRY")" -le 9 ]; then
    rm -f "$ENTRY"
    echo "Bazzite Portal no longer opens at login."
fi
mkdir -p "$(dirname "$STAMP")"
touch "$STAMP"

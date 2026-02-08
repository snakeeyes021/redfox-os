#!/usr/bin/env bash
set -euo pipefail

# Override the Cursor .desktop file to point to our custom icon
# The icon is staged at /usr/share/pixmaps/redfox-cursor.png by the 'files' module

DESKTOP_FILE="/usr/share/applications/cursor.desktop"

if [ -f "$DESKTOP_FILE" ]; then
    echo "Fixing Cursor icon in $DESKTOP_FILE..."
    sed -i 's|Icon=co.anysphere.cursor|Icon=redfox-cursor|g' "$DESKTOP_FILE"
else
    echo "Warning: Cursor desktop file not found at $DESKTOP_FILE" >&2
fi

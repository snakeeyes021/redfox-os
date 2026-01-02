#!/bin/bash
set -e

# We define the version of OUR CONFIGURATION here.
# Increment this number whenever you change the scripts!
CURRENT_CONFIG_VERSION="1"

STATE_FILE="/var/lib/bluebuild-config-version"

# Read the last version we successfully ran
LAST_RUN_VERSION="0"
if [ -f "$STATE_FILE" ]; then
    LAST_RUN_VERSION=$(cat "$STATE_FILE")
fi

# Compare them
if [ "$CURRENT_CONFIG_VERSION" -le "$LAST_RUN_VERSION" ]; then
    echo "System configuration is up to date (Version $LAST_RUN_VERSION)."
    exit 0
fi

echo "Configuration drift detected. Updating from v$LAST_RUN_VERSION to v$CURRENT_CONFIG_VERSION..."

# --- RUN YOUR SCRIPTS HERE ---
SCRIPT_DIR="/usr/share/firstboot/scripts"
if [ -d "$SCRIPT_DIR" ]; then
    for script in "$SCRIPT_DIR"/*; do
        if [ -x "$script" ]; then
            echo "Running $script..."
            "$script" || echo "WARNING: $script failed!"
        fi
    done
fi
# -----------------------------

# Update the state file
echo "$CURRENT_CONFIG_VERSION" > "$STATE_FILE"
echo "Configuration update complete."

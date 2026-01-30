#!/usr/bin/bash
set -euo pipefail

# TARGET: Bazzite's default master configuration
# We modify this in place during build so it works out-of-the-box for all users.
CONFIG_FILE="/usr/share/ublue-os/topgrade.toml"

# Fallback: If the structure changed, find where the file actually is
if [ ! -f "$CONFIG_FILE" ]; then
    CONFIG_FILE=$(find /usr/share -name topgrade.toml | head -n 1)
    if [ -z "$CONFIG_FILE" ]; then
        echo "Error: Could not locate topgrade.toml to inject configuration."
        exit 1
    fi
fi

# CONFIGURATION: The command to inject
# We use [commands] as that is the correct Topgrade syntax for shell hooks
SECTION="[commands]"
INJECTION_GEARLEVER='"Gearlever" = "just update-appimages"'
INJECTION_SOUNDTHREAD='"SoundThread" = "just install-soundthread"'

echo "Injecting Custom Updates into $CONFIG_FILE..."

# IDEMPOTENCY CHECK & INJECTION
# We check and inject each line individually to be safe

# Helper function to inject if missing
inject_line() {
    local line="$1"
    if grep -qF "$line" "$CONFIG_FILE"; then
        echo "Configuration '$line' already present. Skipping."
    else
        # If [commands] exists, insert our line immediately after it
        if grep -qF "$SECTION" "$CONFIG_FILE"; then
            sed -i "/^\[commands\]/a $line" "$CONFIG_FILE"
        else
            # If the section is missing, append the block to the end of the file
            echo "" >> "$CONFIG_FILE"
            echo "$SECTION" >> "$CONFIG_FILE"
            echo "$line" >> "$CONFIG_FILE"
        fi
        echo "Injected: $line"
    fi
}

inject_line "$INJECTION_GEARLEVER"
inject_line "$INJECTION_SOUNDTHREAD"

echo "Success: Custom updates injection complete."
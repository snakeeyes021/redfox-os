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
# We use [custom_commands] as that is the correct Topgrade syntax for shell hooks
SECTION="[custom_commands]"
INJECTION='"Gearlever" = "just update-gearlever"'

echo "Injecting Gearlever update into $CONFIG_FILE..."

# IDEMPOTENCY CHECK: Don't inject if it's already there
if grep -qF "$INJECTION" "$CONFIG_FILE"; then
    echo "Configuration already present. Skipping."
    exit 0
fi

# INJECTION LOGIC
if grep -qF "$SECTION" "$CONFIG_FILE"; then
    # If [custom_commands] exists, insert our line immediately after it
    sed -i "/^\[custom_commands\]/a $INJECTION" "$CONFIG_FILE"
else
    # If the section is missing, append the block to the end of the file
    echo "" >> "$CONFIG_FILE"
    echo "$SECTION" >> "$CONFIG_FILE"
    echo "$INJECTION" >> "$CONFIG_FILE"
fi

echo "Success: Gearlever injection complete."
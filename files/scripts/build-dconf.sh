#!/bin/bash
set -ouex pipefail

PROFILE_FILE="/etc/dconf/profile/user"

# If file doesn't exist, create a basic one
if [ ! -f "$PROFILE_FILE" ]; then
    echo "user-db:user" > "$PROFILE_FILE"
    echo "system-db:local" >> "$PROFILE_FILE" # Assuming this as a fallback
fi

# Inject samsonite if not present
if ! grep -q "system-db:samsonite" "$PROFILE_FILE"; then
    sed -i '/user-db:user/a system-db:samsonite' "$PROFILE_FILE"
fi

# Compile the dconf databases
dconf update

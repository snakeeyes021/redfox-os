#!/bin/bash
set -ouex pipefail

PROFILE_FILE="/etc/dconf/profile/user"

# If file doesn't exist, create a basic one
# If file doesn't exist or is empty, create a basic one.
if [ ! -s "$PROFILE_FILE" ]; then
    echo "user-db:user" > "$PROFILE_FILE"
    echo "system-db:local" >> "$PROFILE_FILE" # Assuming this as a fallback
# Otherwise, ensure user-db:user is present.
elif ! grep -q "^user-db:user" "$PROFILE_FILE"; then
    sed -i '1i user-db:user' "$PROFILE_FILE"
fi

# Inject redfox if not present
if ! grep -q "^system-db:redfox" "$PROFILE_FILE"; then
    sed -i '/^user-db:user/a system-db:redfox' "$PROFILE_FILE"
fi

# Compile the dconf databases
dconf update

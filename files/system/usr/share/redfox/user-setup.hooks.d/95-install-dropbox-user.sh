#!/usr/bin/bash

# Check if the proprietary daemon already exists in the user's home
if [ ! -d "$HOME/.dropbox-dist" ]; then
    echo "Installing Dropbox daemon from local cache..."
    # Copy from the read-only image to the writable home directory
    cp -r /usr/share/dropbox-daemon-cache/.dropbox-dist "$HOME/"
fi

# Dropbox Fix: Force daemon to see /var/home (Btrfs) instead of /home (symlink)
# Targets both Autostart (login) and Local Applications (manual launch/app drawer)

DROPBOX_SOURCE="/usr/share/applications/dropbox.desktop"
TARGETS=(
    "$HOME/.config/autostart/dropbox.desktop"
    "$HOME/.local/share/applications/dropbox.desktop"
)

for TARGET in "${TARGETS[@]}"; do
    # 1. Ensure the directory exists
    mkdir -p "$(dirname "$TARGET")"

    # 2. Copy the system desktop file if the user version is missing
    if [ ! -f "$TARGET" ] && [ -f "$DROPBOX_SOURCE" ]; then
        cp "$DROPBOX_SOURCE" "$TARGET"
    fi

    # 3. Patch the Exec line if it hasn't been patched yet
    # Prevents "Move Dropbox" dialog by forcing HOME=/var/home/...
    if [ -f "$TARGET" ]; then
        # Check if we already patched it to avoid duplicate edits
        if ! grep -q "var/home" "$TARGET"; then
             sed -i "s|^Exec=.*|Exec=sh -c \"HOME='/var/home/\$USER' dropbox start -i\"|" "$TARGET"
        fi
    fi
done

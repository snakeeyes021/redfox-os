#!/usr/bin/env bash

# Exit if there are any errors
set -oue pipefail

echo "Installing smooth-overview extension from GitHub..."

REPO_URL="https://github.com/snakeeyes021/smooth-overview"
TEMP_DIR="/tmp/smooth-overview"

# 1. Clone the repository
git clone --depth 1 "$REPO_URL" "$TEMP_DIR"

# 2. Extract UUID from metadata.json
# We'll use a simple grep/sed to avoid dependency on jq if it's not present
UUID=$(grep -Po '(?<="uuid": ")[^"]*' "$TEMP_DIR/metadata.json")

if [ -z "$UUID" ]; then
    echo "Error: Could not find UUID in metadata.json"
    exit 1
fi

echo "Extension UUID: $UUID"

# 3. Create the system-wide extension directory
INSTALL_DIR="/usr/share/gnome-shell/extensions/$UUID"
mkdir -p "$INSTALL_DIR"

# 4. Copy the extension files
# We use -T to treat destination as a directory and overwrite it
cp -rT "$TEMP_DIR" "$INSTALL_DIR"

# 5. Compile schemas if they exist
if [ -d "$INSTALL_DIR/schemas" ]; then
    echo "Compiling schemas..."
    glib-compile-schemas "$INSTALL_DIR/schemas"
fi

# 6. Set permissions (standard for /usr/share)
chmod -R 755 "$INSTALL_DIR"

# 7. Cleanup
rm -rf "$TEMP_DIR"

echo "smooth-overview extension installed successfully."

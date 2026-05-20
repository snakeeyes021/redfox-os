#!/usr/bin/env bash
set -oue pipefail

echo "Resolving dynamic download URLs for Antigravity from JSON API..."

# Fetch the JSON manifest
JSON_MANIFEST=$(curl -sSL "https://antigravity-auto-updater-974169037036.us-central1.run.app/releases")

# Extract version and execution_id from the latest release (first item)
VERSION=$(echo "$JSON_MANIFEST" | jq -r '.[0].version')
EXEC_ID=$(echo "$JSON_MANIFEST" | jq -r '.[0].execution_id')

if [ -z "$VERSION" ] || [ "$VERSION" == "null" ] || [ -z "$EXEC_ID" ] || [ "$EXEC_ID" == "null" ]; then
    echo "ERROR: Failed to parse version or execution_id from JSON manifest."
    echo "JSON Payload was: $JSON_MANIFEST"
    exit 1
fi

URL_20="https://storage.googleapis.com/antigravity-public/antigravity-hub/${VERSION}-${EXEC_ID}/linux-x64/Antigravity.tar.gz"
URL_IDE="https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/${VERSION}-${EXEC_ID}/linux-x64/Antigravity%20IDE.tar.gz"

echo "Resolved Antigravity 2.0: $URL_20"
echo "Resolved Antigravity IDE: $URL_IDE"

echo "Downloading Antigravity 2.0..."
curl -L -o /tmp/Antigravity.tar.gz "$URL_20"

echo "Downloading Antigravity IDE..."
curl -L -o /tmp/Antigravity-IDE.tar.gz "$URL_IDE"

echo "Extracting Antigravity 2.0..."
mkdir -p /usr/lib/antigravity
rm -rf /usr/lib/antigravity/*
if ! tar -xzf /tmp/Antigravity.tar.gz -C /usr/lib/antigravity --strip-components=1 2>/dev/null; then
    tar -xzf /tmp/Antigravity.tar.gz -C /usr/lib/antigravity
fi

echo "Extracting Antigravity IDE..."
mkdir -p /usr/lib/antigravity-ide
rm -rf /usr/lib/antigravity-ide/*
if ! tar -xzf /tmp/Antigravity-IDE.tar.gz -C /usr/lib/antigravity-ide --strip-components=1 2>/dev/null; then
    tar -xzf /tmp/Antigravity-IDE.tar.gz -C /usr/lib/antigravity-ide
fi

echo "Setting executable permissions..."
chmod +x /usr/lib/antigravity/antigravity 2>/dev/null || true
chmod +x /usr/lib/antigravity/bin/* 2>/dev/null || true
chmod +x "/usr/lib/antigravity-ide/Antigravity IDE" 2>/dev/null || true
chmod +x /usr/lib/antigravity-ide/antigravity-ide 2>/dev/null || true
chmod +x /usr/lib/antigravity-ide/bin/* 2>/dev/null || true

echo "Installing icon..."
ICON_FILE=$(find /usr/lib/antigravity-ide -type f \( -iname "*.png" -o -iname "*.svg" \) | grep -i icon | head -n 1)
if [ -z "$ICON_FILE" ]; then
    ICON_FILE=$(find /usr/lib/antigravity-ide -type f \( -iname "*.png" -o -iname "*.svg" \) | head -n 1)
fi
if [ -n "$ICON_FILE" ]; then
    mkdir -p /usr/share/pixmaps
    cp "$ICON_FILE" "/usr/share/pixmaps/antigravity-ide.${ICON_FILE##*.}"
fi

echo "Creating symlinks..."
if [ -f /usr/lib/antigravity/antigravity ]; then
    ln -sf /usr/lib/antigravity/antigravity /usr/bin/antigravity
elif [ -f /usr/lib/antigravity/bin/antigravity ]; then
    ln -sf /usr/lib/antigravity/bin/antigravity /usr/bin/antigravity
else
    echo "ERROR: Could not find Antigravity 2.0 binary to symlink!"
    exit 1
fi

if [ -f "/usr/lib/antigravity-ide/Antigravity IDE" ]; then
    ln -sf "/usr/lib/antigravity-ide/Antigravity IDE" /usr/bin/antigravity-ide
elif [ -f /usr/lib/antigravity-ide/antigravity-ide ]; then
    ln -sf /usr/lib/antigravity-ide/antigravity-ide /usr/bin/antigravity-ide
elif [ -f /usr/lib/antigravity-ide/bin/antigravity-ide ]; then
    ln -sf /usr/lib/antigravity-ide/bin/antigravity-ide /usr/bin/antigravity-ide
else
    echo "ERROR: Could not find Antigravity IDE binary to symlink!"
    exit 1
fi

# Desktop Entry for IDE
cat << 'EOF' > /usr/share/applications/antigravity-ide.desktop
[Desktop Entry]
Name=Antigravity IDE
Exec=/usr/bin/antigravity-ide
Terminal=false
Type=Application
Categories=Development;IDE;
Icon=antigravity-ide
EOF

rm -f /tmp/Antigravity.tar.gz /tmp/Antigravity-IDE.tar.gz
echo "Antigravity installed successfully!"

#!/usr/bin/env bash
set -euo pipefail

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

# Temporarily hardcoding the IDE URL since there doesn't appear to be any programmatic way to retrieve it, no JSON manifest, no API endpoint, no scrapable download page, etc.
# We can revisit if they eventually include it in a repo like they used to. For now we'll just update this URL every so often.
URL_IDE="https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/2.1.1-6123990880747520/linux-x64/Antigravity%20IDE.tar.gz"

echo "Resolved Antigravity 2.0: $URL_20"
echo "Resolved Antigravity IDE: $URL_IDE"

echo "Downloading Antigravity 2.0..."
curl -fL -o /tmp/Antigravity.tar.gz "$URL_20"

echo "Downloading Antigravity IDE..."
curl -fL -o /tmp/Antigravity-IDE.tar.gz "$URL_IDE"

echo "Extracting Antigravity 2.0..."
mkdir -p /usr/lib/antigravity
rm -rf /usr/lib/antigravity/*
tar -xzf /tmp/Antigravity.tar.gz -C /usr/lib/antigravity --strip-components=1

echo "Extracting Antigravity IDE..."
mkdir -p /usr/lib/antigravity-ide
rm -rf /usr/lib/antigravity-ide/*
tar -xzf /tmp/Antigravity-IDE.tar.gz -C /usr/lib/antigravity-ide --strip-components=1

echo "Setting executable permissions..."
chmod +x /usr/lib/antigravity/antigravity 2>/dev/null || true
chmod +x /usr/lib/antigravity/bin/* 2>/dev/null || true
chmod +x "/usr/lib/antigravity-ide/Antigravity IDE" 2>/dev/null || true
chmod +x /usr/lib/antigravity-ide/antigravity-ide 2>/dev/null || true
chmod +x /usr/lib/antigravity-ide/bin/* 2>/dev/null || true

echo "Installing icons..."
# Ensure 7z is installed
if ! command -v 7z &> /dev/null; then
    echo "7z not found, trying to install p7zip..."
    if command -v dnf &> /dev/null; then
        dnf install -y p7zip p7zip-plugins
    elif command -v microdnf &> /dev/null; then
        microdnf install -y p7zip p7zip-plugins
    elif command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y p7zip-full
    else
        echo "WARNING: Could not find dnf, microdnf, or apt-get to install p7zip/7z. Extraction might fail."
    fi
fi

# Download macOS DMGs to get the high-resolution icons
echo "Downloading Antigravity 2.0 DMG for high-res icon..."
curl -fL -o /tmp/Antigravity.dmg "https://storage.googleapis.com/antigravity-public/antigravity-hub/2.0.1-6566078776737792/darwin-arm/Antigravity.dmg"

echo "Downloading Antigravity IDE DMG for high-res icon..."
curl -fL -o /tmp/Antigravity-IDE.dmg "https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/2.0.1-4861014005645312/darwin-arm/Antigravity%20IDE.dmg"

# Extract the .icns files from the DMGs
echo "Extracting icon files..."
7z e -y /tmp/Antigravity.dmg -o/tmp "Antigravity 2.0.1-arm64/Antigravity.app/Contents/Resources/icon.icns"
7z e -y /tmp/Antigravity-IDE.dmg -o/tmp "Antigravity IDE/Antigravity IDE.app/Contents/Resources/Antigravity IDE.icns"

# Parse the .icns files and extract the largest PNG from each
mkdir -p /usr/share/pixmaps
python3 -c '
import struct
import sys

def extract_largest_png(icns_path, output_png_path):
    try:
        with open(icns_path, "rb") as f:
            magic, total_len = struct.unpack(">4sI", f.read(8))
            if magic != b"icns":
                print(f"Error: {icns_path} is not a valid icns file", file=sys.stderr)
                return False
            
            largest_size = 0
            largest_data = None
            
            while f.tell() < total_len:
                b_type, b_len = struct.unpack(">4sI", f.read(8))
                if b_len < 8:
                    break
                b_data = f.read(b_len - 8)
                
                if b_data.startswith(b"\x89PNG\r\n\x1a\n"):
                    if len(b_data) >= 24:
                        w, h = struct.unpack(">II", b_data[16:24])
                        size = w * h
                        if size > largest_size:
                            largest_size = size
                            largest_data = b_data
            
            if largest_data:
                with open(output_png_path, "wb") as out_f:
                    out_f.write(largest_data)
                print(f"Successfully extracted largest PNG ({largest_size**0.5:.0f}x{largest_size**0.5:.0f}) to {output_png_path}")
                return True
            else:
                print(f"Error: No PNG icon found in {icns_path}", file=sys.stderr)
                return False
    except Exception as e:
        print(f"Error processing {icns_path}: {e}", file=sys.stderr)
        return False

extract_largest_png("/tmp/icon.icns", "/usr/share/pixmaps/antigravity.png")
extract_largest_png("/tmp/Antigravity IDE.icns", "/usr/share/pixmaps/antigravity-ide.png")
'

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

# Desktop Entry for Antigravity 2.0
cat << 'EOF' > /usr/share/applications/antigravity.desktop
[Desktop Entry]
Name=Antigravity
Exec=/usr/bin/antigravity
Terminal=false
Type=Application
Categories=Utility;
Icon=antigravity
EOF

rm -f /tmp/Antigravity.tar.gz /tmp/Antigravity-IDE.tar.gz /tmp/Antigravity.dmg /tmp/Antigravity-IDE.dmg /tmp/icon.icns "/tmp/Antigravity IDE.icns"
echo "Antigravity installed successfully!"

#!/usr/bin/bash
set -ouex pipefail

# The Official URL
URL="https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-x86_64.tgz"

# Its expected hash
EXPECTED_HASH="5690596c54ff9bed63fa3732f818a05dbc2db19ad36ed68f21ca5f64d5cfeeb7" 

# Create temp space
TEMP_DIR=$(mktemp -d)
downloaded_file="$TEMP_DIR/speedtest.tgz"

echo "Downloading Ookla Speedtest CLI..."
curl -fL "$URL" -o "$downloaded_file"

echo "Verifying integrity..."
calculated_hash=$(sha256sum "$downloaded_file" | awk '{print $1}')

if [ "$calculated_hash" != "$EXPECTED_HASH" ]; then
    echo "ERROR: Hash mismatch!"
    echo "Expected: $EXPECTED_HASH"
    echo "Got:      $calculated_hash"
    echo "The file may have been tampered with or updated by Ookla."
    exit 1
fi

echo "Hash verified. Installing..."
tar -xzf "$downloaded_file" -C "$TEMP_DIR" speedtest
install -m 755 "$TEMP_DIR/speedtest" /usr/bin/speedtest

# Cleanup
rm -rf "$TEMP_DIR"

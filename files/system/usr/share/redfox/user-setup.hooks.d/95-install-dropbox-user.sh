#!/usr/bin/bash

# Check if the proprietary daemon already exists in the user's home
if [ ! -d "$HOME/.dropbox-dist" ]; then
    echo "Installing Dropbox daemon from local cache..."
    # Copy from the read-only image to the writable home directory
    cp -r /usr/share/dropbox-daemon-cache/.dropbox-dist "$HOME/"
fi

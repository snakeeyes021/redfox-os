#!/usr/bin/env bash
set -oue pipefail

# create a cache directory in /usr/share
mkdir -p /usr/share/dropbox-daemon-cache

# Download and extract the daemon there
wget -O - "https://www.dropbox.com/download?plat=lnx.x86_64" | tar xzf - -C /usr/share/dropbox-daemon-cache/

# Result: You now have /usr/share/dropbox-daemon-cache/.dropbox-dist

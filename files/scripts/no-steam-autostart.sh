#!/usr/bin/env bash
# Steam doesn't start by itself at login on a new RedFoxOS install: new
# accounts don't get Bazzite's autostart entry for it. It's a switch in
# RedFox Hub › Settings › Start at Login (redfox-autostart on steam).
# Accounts that already have the entry keep it, and Hub shows it as on.
set -euo pipefail

rm -f /etc/skel/.config/autostart/steam.desktop

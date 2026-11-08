#!/usr/bin/env bash
# Bazzite Portal (the first-run app) doesn't open by itself on RedFoxOS: new
# accounts don't get its autostart entry. It can still be opened from the app
# grid. Accounts that already have the entry lose it once at their next login
# (user-setup hook 40-no-bazzite-portal-autostart.sh).
set -euo pipefail

rm -f /etc/skel/.config/autostart/bazzite-portal.desktop

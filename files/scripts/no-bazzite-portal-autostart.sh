#!/usr/bin/env bash
# Bazzite Portal (the first-run app) isn't part of RedFoxOS: RedFox Hub does
# its job. The package is removed in the recipe; this removes what it leaves
# behind: its settings and new accounts' autostart entry. Accounts that
# already have the entry lose it once at their next login (user-setup hook
# 40-no-bazzite-portal-autostart.sh).
set -euo pipefail

rm -f /etc/skel/.config/autostart/bazzite-portal.desktop
rm -rf /usr/share/yafti

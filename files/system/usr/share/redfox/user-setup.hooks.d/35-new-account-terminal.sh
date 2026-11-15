#!/usr/bin/bash
# New accounts start with the terminal's styled prompt on, in the Catppuccin
# Powerline theme (the terminal itself follows the desktop's light or dark
# style for everyone, from RedFox's settings defaults). Only accounts made on
# RedFoxOS have the marker (from /etc/skel), so an existing account's terminal
# is left alone. The prompt's Starship comes from Homebrew: if that isn't
# ready yet (or belongs to another account that hasn't installed it), the
# marker stays and it's tried again at the next login. It can be changed any
# time in RedFox Hub › Terminal.

set -euo pipefail

MARKER="${XDG_CONFIG_HOME:-$HOME/.config}/redfox/new-account-terminal"

[ -e "$MARKER" ] || exit 0
if redfox-terminal prompt theme catppuccin-powerline; then
    rm -f -- "$MARKER"
    echo "Turned on the terminal's styled prompt."
else
    echo "The terminal's styled prompt isn't on yet; trying again next login."
fi

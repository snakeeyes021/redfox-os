#!/usr/bin/bash

# 1. Create the destination folder first
mkdir -p "$HOME"/.local/share/themes/

# 2. Copy both themes into that folder
cp -ru /usr/share/themes/adw-gtk3* "$HOME"/.local/share/themes/

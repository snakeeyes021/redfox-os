#!/usr/bin/env bash
set -euo pipefail

echo "Patching Insync Nautilus plugin for GTK4 compatibility..."

# Inject the missing version declaration right before the Gdk import
sed -i '/from gi.repository import Gdk/i gi.require_version("Gdk", "4.0")' /usr/share/nautilus-python/extensions/insync-nautilus-plugin.py

echo "Insync patch applied successfully."
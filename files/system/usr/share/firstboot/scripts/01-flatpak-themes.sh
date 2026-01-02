#!/bin/bash
# Apply Flatpak overrides system-wide
flatpak override --filesystem=xdg-data/themes
flatpak mask org.gtk.Gtk3theme.adw-gtk3
flatpak mask org.gtk.Gtk3theme.adw-gtk3-dark

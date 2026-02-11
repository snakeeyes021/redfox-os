#!/usr/bin/bash
# 90-redfox-setup.sh
# RedFoxOS User Setup Hook
# Handles mandatory extensions and default settings for VSCode and Cursor.

set -euo pipefail

# --- VS CODE SETUP ---

if command -v code &> /dev/null; then
    # VSCode Mandatory Extensions
    VSCODE_EXTENSIONS=(
        "ms-vscode-remote.remote-containers"
        "ms-vscode-remote.remote-ssh"
        "ms-azuretools.vscode-containers"
    )

    for ext_id in "${VSCODE_EXTENSIONS[@]}"; do
        # Check if extension exists in ~/.vscode/extensions/ (case-insensitive check handled by glob)
        # We look for a directory starting with the extension ID (lowercase)
        if ! compgen -G "$HOME/.vscode/extensions/${ext_id,,}*" > /dev/null; then
             echo "Installing VSCode extension: $ext_id"
             code --install-extension "$ext_id" --force > /dev/null 2>&1 || echo "Failed to install $ext_id"
        fi
    done

    # VSCode Default Settings (One-time copy)
    VSCODE_USER_SETTINGS="$HOME/.config/Code/User/settings.json"
    VSCODE_SKELETON="/etc/skel/.config/Code/User/settings.json"

    if [ ! -f "$VSCODE_USER_SETTINGS" ]; then
        if [ -f "$VSCODE_SKELETON" ]; then
            echo "Initializing VSCode settings..."
            mkdir -p "$(dirname "$VSCODE_USER_SETTINGS")"
            cp "$VSCODE_SKELETON" "$VSCODE_USER_SETTINGS"
        fi
    fi
fi


# --- CURSOR SETUP ---

if command -v cursor &> /dev/null; then
    # Cursor Mandatory Extensions
    CURSOR_EXTENSIONS=(
        "ms-vscode-remote.remote-containers"
        "ms-vscode-remote.remote-ssh"
        "ms-azuretools.vscode-containers"
    )

    for ext_id in "${CURSOR_EXTENSIONS[@]}"; do
        # Check if extension exists in ~/.cursor/extensions/
        if ! compgen -G "$HOME/.cursor/extensions/${ext_id,,}*" > /dev/null; then
             echo "Installing Cursor extension: $ext_id"
             cursor --install-extension "$ext_id" --force > /dev/null 2>&1 || echo "Failed to install $ext_id"
        fi
    done

    # Cursor Default Settings (One-time copy)
    CURSOR_USER_SETTINGS="$HOME/.config/Cursor/User/settings.json"
    CURSOR_SKELETON="/etc/skel/.config/Cursor/User/settings.json"

    if [ ! -f "$CURSOR_USER_SETTINGS" ]; then
        if [ -f "$CURSOR_SKELETON" ]; then
            echo "Initializing Cursor settings..."
            mkdir -p "$(dirname "$CURSOR_USER_SETTINGS")"
            cp "$CURSOR_SKELETON" "$CURSOR_USER_SETTINGS"
        fi
    fi
fi

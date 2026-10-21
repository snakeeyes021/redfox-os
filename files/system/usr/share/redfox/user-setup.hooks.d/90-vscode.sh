#!/usr/bin/bash
# 90-redfox-setup.sh
# RedFoxOS User Setup Hook
# Handles mandatory extensions and default settings for VSCode, Cursor, and Antigravity IDE.

set -euo pipefail

# --- VS CODE SETUP ---

if command -v code &> /dev/null; then
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

    # VSCode Mandatory Extensions
    VSCODE_EXTENSIONS=(
        "ms-vscode-remote.remote-containers"
        "ms-vscode-remote.remote-ssh"
        "ms-azuretools.vscode-containers"
    )

    for ext_id in "${VSCODE_EXTENSIONS[@]}"; do
        # Check if extension exists in ~/.vscode/extensions/ (case-insensitive check handled by glob)
        if ! compgen -G "$HOME/.vscode/extensions/${ext_id,,}*" > /dev/null; then
             echo "Installing VSCode extension: $ext_id"
             code --install-extension "$ext_id" --force > /dev/null 2>&1 || echo "Failed to install $ext_id"
        fi
    done
fi


# --- CURSOR SETUP ---

if command -v cursor &> /dev/null; then
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
fi


# --- ANTIGRAVITY IDE SETUP ---

if [ -x "/usr/lib/antigravity-ide/bin/antigravity-ide" ]; then
    ANTIGRAVITY_BIN="/usr/lib/antigravity-ide/bin/antigravity-ide"

    # Antigravity IDE Default Settings (One-time copy)
    ANTIGRAVITY_USER_SETTINGS="$HOME/.config/Antigravity IDE/User/settings.json"
    ANTIGRAVITY_SKELETON="/etc/skel/.config/Antigravity IDE/User/settings.json"

    if [ ! -f "$ANTIGRAVITY_USER_SETTINGS" ]; then
        if [ -f "$ANTIGRAVITY_SKELETON" ]; then
            echo "Initializing Antigravity IDE settings..."
            mkdir -p "$(dirname "$ANTIGRAVITY_USER_SETTINGS")"
            cp "$ANTIGRAVITY_SKELETON" "$ANTIGRAVITY_USER_SETTINGS"
        fi
    fi

    # Antigravity IDE Mandatory Extensions
    ANTIGRAVITY_EXTENSIONS=(
        "ms-vscode-remote.remote-containers"
        "ms-vscode-remote.remote-ssh"
        "ms-azuretools.vscode-containers"
    )

    for ext_id in "${ANTIGRAVITY_EXTENSIONS[@]}"; do
        # Check if extension exists in ~/.antigravity-ide/extensions/
        if ! compgen -G "$HOME/.antigravity-ide/extensions/${ext_id,,}*" > /dev/null; then
             echo "Installing Antigravity IDE extension: $ext_id"
             "$ANTIGRAVITY_BIN" --install-extension "$ext_id" --force > /dev/null 2>&1 || echo "Failed to install $ext_id"
        fi
    done
fi

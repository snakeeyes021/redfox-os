#!/usr/bin/bash
# 90-redfox-setup.sh
# RedFoxOS User Setup Hook
# Handles mandatory extensions and default settings for VSCode and Cursor.

set -euo pipefail

# Install an extension straight from Open VSX as a .vsix. For forks whose
# own marketplace doesn't carry it (Cursor's mirror returns 403 for some
# Open VSX extensions).
install_from_openvsx() {
    local editor="$1" ext_id="$2" url vsix
    url="$(curl -fsSL "https://open-vsx.org/api/${ext_id%%.*}/${ext_id#*.}" |
        python3 -c 'import json, sys; print(json.load(sys.stdin)["files"]["download"])' 2>/dev/null)" || return 1
    vsix="$(mktemp --suffix=.vsix)"
    curl -fsSL -o "$vsix" "$url" && "$editor" --install-extension "$vsix" --force > /dev/null 2>&1
    local status=$?
    rm -f "$vsix"
    return $status
}

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
        "Google.google-antigravity"
        "RedFoxLabs.dewy"
        "RedFoxLabs.sloppy"
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

    # Cursor Mandatory Extensions. Cursor swaps Microsoft's remote extensions
    # for its own (anysphere.*), so ask for those: asking for Microsoft's ids
    # never found them installed and reinstalled both at every login.
    CURSOR_EXTENSIONS=(
        "anysphere.remote-containers"
        "anysphere.remote-ssh"
        "ms-azuretools.vscode-containers"
        "RedFoxLabs.dewy"
        "RedFoxLabs.sloppy"
    )

    for ext_id in "${CURSOR_EXTENSIONS[@]}"; do
        # Check if extension exists in ~/.cursor/extensions/
        if ! compgen -G "$HOME/.cursor/extensions/${ext_id,,}*" > /dev/null; then
             echo "Installing Cursor extension: $ext_id"
             cursor --install-extension "$ext_id" --force > /dev/null 2>&1 ||
                 install_from_openvsx cursor "$ext_id" ||
                 echo "Failed to install $ext_id"
        fi
    done
fi

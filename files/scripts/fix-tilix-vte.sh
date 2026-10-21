#!/bin/bash
set -ouex pipefail

# --- Bash Integration ---
# Append logic to /etc/bashrc if it isn't already there.
if ! grep -q "Tilix VTE integration" /etc/bashrc; then
    echo "Patching /etc/bashrc for Tilix VTE support..."
    cat <<'EOF' >> /etc/bashrc

# Tilix VTE integration
if [ -n "${TILIX_ID:-}" ] && [ -f /etc/profile.d/vte.sh ]; then
    source /etc/profile.d/vte.sh
fi
EOF
fi

# --- Zsh Integration ---
# Fedora/Bazzite typically uses /etc/zshrc.
ZSHRC_LOC="/etc/zshrc"

if [ -f "$ZSHRC_LOC" ] && ! grep -q "Tilix VTE integration" "$ZSHRC_LOC"; then
    echo "Patching $ZSHRC_LOC for Tilix VTE support..."
    cat <<'EOF' >> "$ZSHRC_LOC"

# Tilix VTE integration
if [[ -n "${TILIX_ID:-}" ]] && [[ -f /etc/profile.d/vte.sh ]]; then
    source /etc/profile.d/vte.sh
fi
EOF
fi

# Level 1: Atoms (Single-Purpose Scripts)

# Setup System Configuration (The "Front Desk" Pattern)
# This recipe is the first dependency for any recipe chain requiring private configuration or hardware quirks.
# Ensures ~/.config/redfox/config.yaml is present. Headless-safe: skips gracefully with recap ledger.
redfox-enforce-config:
    #!/usr/bin/bash
    set -euo pipefail
    CONFIG_FILE="$HOME/.config/redfox/config.yaml"
    LOG_FILE="${XDG_RUNTIME_DIR:-$HOME/.cache}/redfox-bootstrap-current.log"

    if [ -s "$CONFIG_FILE" ]; then
        exit 0
    fi

    if [ ! -t 0 ]; then
        echo "- System configuration skipped (Headless mode, using defaults)" >> "$LOG_FILE"
        exit 0
    fi

    # Interactive prompt via redfox-config setup
    /usr/bin/redfox-config setup || true

# Interactively setup or update configuration (paste, file, or URL)
redfox-setup-config:
    /usr/bin/redfox-config setup

# Edit configuration file in text editor
redfox-edit-config:
    /usr/bin/redfox-config edit

# Starts a fresh ledger for this bootstrap run
_reset-bootstrap-recap:
    rm -f "${XDG_RUNTIME_DIR:-$HOME/.cache}/redfox-bootstrap-current.log"

# Evaluates the run and archives the ledger
_print-bootstrap-recap:
    #!/usr/bin/bash
    LOG_FILE="${XDG_RUNTIME_DIR:-$HOME/.cache}/redfox-bootstrap-current.log"
    ARCHIVE_DIR="$HOME/.local/state/redfox"
    
    echo ""
    echo "================================================================="
    if [ -f "$LOG_FILE" ]; then
        echo " ⚠️  Bootstrap Complete (With Skipped Items)"
        echo "================================================================="
        cat "$LOG_FILE"
        echo "-----------------------------------------------------------------"
        echo " You can configure these later by running: ujust redfox-edit-config"
        
        mkdir -p "$ARCHIVE_DIR"
        mv "$LOG_FILE" "$ARCHIVE_DIR/bootstrap-$(date +%Y%m%d-%H%M%S).log"
    else
        echo " 🎉 Bootstrap Complete! All systems go."
        echo "================================================================="
    fi

# Permanently delete all saved configuration files
redfox-reset-config:
    /usr/bin/redfox-config reset

# This machine's name from config.yaml (machines.<id>.hostname); otherwise "redfox"
# if the name is still an upstream default. A name you picked is never changed.
# Set the computer's name (from config.yaml, or "redfox" in place of an upstream default)
reset-hostname:
    #!/usr/bin/bash
    set -euo pipefail
    NAME=""
    if /usr/bin/redfox-config get machines &>/dev/null; then
        # Board/model names are readable without root; only read the DMI serial (sudo) if they don't match
        NAME=$(/usr/bin/redfox-config machine hostname 2>/dev/null || true)
        if [ -z "$NAME" ]; then
            SERIAL=$(sudo cat /sys/class/dmi/id/product_serial 2>/dev/null || true)
            NAME=$(/usr/bin/redfox-config machine hostname --id "$SERIAL" 2>/dev/null || true)
        fi
    fi
    CURRENT=$(hostnamectl hostname 2>/dev/null || hostname)
    PRETTY="$NAME"
    if [ -z "$NAME" ]; then
        case "$CURRENT" in
            bazzite|fedora|localhost|localhost.localdomain|localhost-live|"")
                NAME="redfox"
                PRETTY="RedFoxOS"
                ;;
            *)
                echo "[OK] Keeping hostname '$CURRENT' (no machines entry for this device in config.yaml)."
                exit 0
                ;;
        esac
    fi
    if [ "$CURRENT" = "$NAME" ]; then
        echo "[OK] Hostname is already '$NAME'."
        exit 0
    fi
    echo "Setting hostname to $NAME..."
    hostnamectl set-hostname "$NAME"
    hostnamectl set-hostname --pretty "$PRETTY"
    echo "Done! Please reboot for all changes to take full effect."

# Configure Git
configure-git:
    echo "TODO: Implement configure-git"

# Configure VSCode
configure-vscode:
    echo "TODO: Implement configure-vscode"

# Configure Cursor
configure-cursor:
    echo "TODO: Implement configure-cursor"

# Configure Text Editor Dev Mode (Indentation)
configure-text-editor-dev:
    #!/usr/bin/bash
    set -euo pipefail
    if ! flatpak info org.gnome.TextEditor &>/dev/null; then
        echo "GNOME Text Editor (Flatpak) is not installed. Skipping."
        exit 0
    fi
    echo "Configuring Text Editor for Development (Spaces, 4 per tab)..."
    flatpak run --command=gsettings org.gnome.TextEditor set org.gnome.TextEditor indent-style 'space'
    flatpak run --command=gsettings org.gnome.TextEditor set org.gnome.TextEditor tab-width 4
    flatpak run --command=gsettings org.gnome.TextEditor set org.gnome.TextEditor restore-session false

# Reset Text Editor Configuration (Indentation)
configure-text-editor-reset:
    #!/usr/bin/bash
    set -euo pipefail
    if ! flatpak info org.gnome.TextEditor &>/dev/null; then
        echo "GNOME Text Editor (Flatpak) is not installed. Skipping."
        exit 0
    fi
    echo "Resetting Text Editor indentation to defaults..."
    flatpak run --command=gsettings org.gnome.TextEditor reset org.gnome.TextEditor indent-style
    flatpak run --command=gsettings org.gnome.TextEditor reset org.gnome.TextEditor tab-width
    flatpak run --command=gsettings org.gnome.TextEditor reset org.gnome.TextEditor restore-session

# Theme Text Editor Dewy (Visuals)
theme-text-editor-dewy:
    #!/usr/bin/bash
    set -euo pipefail
    if ! flatpak info org.gnome.TextEditor &>/dev/null; then
        echo "GNOME Text Editor (Flatpak) is not installed. Skipping."
        exit 0
    fi
    echo "Configuring Text Editor Visuals (Dark Mode, Line Numbers, Map, Highlight)..."
    flatpak run --command=gsettings org.gnome.TextEditor set org.gnome.TextEditor style-variant 'dark'
    flatpak run --command=gsettings org.gnome.TextEditor set org.gnome.TextEditor show-line-numbers true
    flatpak run --command=gsettings org.gnome.TextEditor set org.gnome.TextEditor show-map true
    flatpak run --command=gsettings org.gnome.TextEditor set org.gnome.TextEditor highlight-current-line true

# Theme Text Editor Default (Visuals Reset)
theme-text-editor-default:
    #!/usr/bin/bash
    set -euo pipefail
    if ! flatpak info org.gnome.TextEditor &>/dev/null; then
        echo "GNOME Text Editor (Flatpak) is not installed. Skipping."
        exit 0
    fi
    echo "Resetting Text Editor visuals to defaults..."
    flatpak run --command=gsettings org.gnome.TextEditor reset org.gnome.TextEditor style-variant
    flatpak run --command=gsettings org.gnome.TextEditor reset org.gnome.TextEditor show-line-numbers
    flatpak run --command=gsettings org.gnome.TextEditor reset org.gnome.TextEditor show-map
    flatpak run --command=gsettings org.gnome.TextEditor reset org.gnome.TextEditor highlight-current-line

# Install Zed
install-zed:
    /usr/bin/redfox-software install zed

# Uninstall Zed
uninstall-zed:
    /usr/bin/redfox-software remove zed

# Install Antigravity CLI
install-antigravity-cli:
    /usr/bin/redfox-software install antigravity-cli

# Uninstall Antigravity CLI
uninstall-antigravity-cli:
    /usr/bin/redfox-software remove antigravity-cli

# Configure Heroic
configure-heroic:
    echo "TODO: Implement configure-heroic"

# Install SoundThread
install-soundthread:
    /usr/bin/redfox-software install soundthread

# Uninstall SoundThread
uninstall-soundthread:
    /usr/bin/redfox-software remove soundthread

# Update all installed RedFox Labs applications
update-redfox-apps:
    /usr/bin/update-redfox-apps

# Install RedFox App Fleet (all RedFox Labs Flatpak applications)
install-redfox-app-fleet:
    /usr/bin/redfox-software install redfox-app-fleet

# Uninstall RedFox App Fleet
uninstall-redfox-app-fleet:
    /usr/bin/redfox-software remove redfox-app-fleet

# Install Pianola (MIDI viewer & archive playback Flatpak)
install-pianola:
    /usr/bin/redfox-software install tech.redfoxlabs.Pianola

# Uninstall Pianola
uninstall-pianola:
    /usr/bin/redfox-software remove tech.redfoxlabs.Pianola

# Install Thirties (half-hour block AI scheduling assistant Flatpak)
install-thirties:
    /usr/bin/redfox-software install tech.redfoxlabs.Thirties

# Uninstall Thirties
uninstall-thirties:
    /usr/bin/redfox-software remove tech.redfoxlabs.Thirties

# Roll back, or move to another RedFoxOS build (latest, unstable, a dated or commit build)
rollback-helper *ARGS:
    /usr/bin/redfox-rollback-helper {{ ARGS }}

# Switch image: the graphics (AMD & Intel, NVIDIA, NVIDIA Legacy) and the channel (latest or unstable). Asks, then confirms.
switch-image *ARGS:
    /usr/bin/redfox-rollback-helper switch-image {{ ARGS }}

# Feature branches with a test build (unsupported, for developers); rebase with: ujust rollback-helper rebase pr-N-FEDORA
list-feature-branches:
    /usr/bin/redfox-rollback-helper branches

# Run the optional Bazzite graphical updater
update-gui:
    #!/usr/bin/bash
    bazzite-updater >/dev/null 2>&1 &

# Update all AppImages managed by Gearlever
update-appimages:
    /usr/bin/update-appimages

# Start Signal and Joplin in the tray at login, if they're installed. Opened any other way, they open normally.
configure-autostart-tray:
    /usr/bin/redfox-autostart on org.signal.Signal net.cozic.joplin_desktop

# Undo configure-autostart-tray
reset-autostart-tray:
    /usr/bin/redfox-autostart off org.signal.Signal net.cozic.joplin_desktop

# UI/UX Atoms
fix-flatpak-theming:
    sudo flatpak override --filesystem=xdg-data/themes
    sudo flatpak mask org.gtk.Gtk3theme.adw-gtk3
    sudo flatpak mask org.gtk.Gtk3theme.adw-gtk3-dark

# Force square corners on all windows (Libadwaita + GTK3 + Flatpak)
theme-square-corners:
    #!/usr/bin/bash
    APP_ID="tech.redfoxlabs.square-corners" # specific ID for tracking changes
    
    # CSS to force square borders
    CSS_CONTENT="
    /* $APP_ID START */
    window, window.background, .window-frame, .titlebar, .dialog, .messagedialog, .csd, decoration { border-radius: 0px; }
    /* $APP_ID END */
    "
    
    # 1. Apply to GTK 4 (Libadwaita)
    GTK4_DIR="$HOME/.config/gtk-4.0"
    mkdir -p "$GTK4_DIR"
    # Remove old block if exists to avoid duplicates, then append
    sed -i "/$APP_ID START/,/$APP_ID END/d" "$GTK4_DIR/gtk.css" 2>/dev/null
    echo "$CSS_CONTENT" >> "$GTK4_DIR/gtk.css"
    
    # 2. Apply to GTK 3
    GTK3_DIR="$HOME/.config/gtk-3.0"
    mkdir -p "$GTK3_DIR"
    sed -i "/$APP_ID START/,/$APP_ID END/d" "$GTK3_DIR/gtk.css" 2>/dev/null
    echo "$CSS_CONTENT" >> "$GTK3_DIR/gtk.css"

    # 3. Expose configs to Flatpak
    # Explicitly allow flatpaks to read ~/.config/gtk-X.0
    flatpak override --user --filesystem=xdg-config/gtk-4.0:ro
    flatpak override --user --filesystem=xdg-config/gtk-3.0:ro
    
    echo "Square corners applied. Please restart your applications or log out/in."

# Revert to default rounded corners
theme-default-corners:
    #!/usr/bin/bash
    APP_ID="tech.redfoxlabs.square-corners"
    
    # 1. Clean GTK 4
    GTK4_FILE="$HOME/.config/gtk-4.0/gtk.css"
    if [ -f "$GTK4_FILE" ]; then
        sed -i "/$APP_ID START/,/$APP_ID END/d" "$GTK4_FILE"
    fi
    
    # 2. Clean GTK 3
    GTK3_FILE="$HOME/.config/gtk-3.0/gtk.css"
    if [ -f "$GTK3_FILE" ]; then
        sed -i "/$APP_ID START/,/$APP_ID END/d" "$GTK3_FILE"
    fi
    
    # Note: We do NOT remove the flatpak overrides here, because 
    # it is harmless (and often beneficial) for Flatpaks to see 
    # user configs even if they are empty.
    
    echo "Reverted to default rounded corners. Please restart your applications."

# Use GNOME's own sound theme
theme-sound-fedora:
    gsettings reset org.gnome.desktop.sound theme-name

theme-sound-bazzite:
    gsettings set org.gnome.desktop.sound theme-name 'steam'

# Window buttons on the right: minimise, maximise and close
set-window-controls-right-full:
    gsettings set org.gnome.desktop.wm.preferences button-layout ':minimize,maximize,close'

# Window buttons on the right: close only
set-window-controls-right-gnome:
    gsettings set org.gnome.desktop.wm.preferences button-layout ':close'

# Window buttons back to the default: close, on the left
set-window-controls-left-gnome:
    gsettings reset org.gnome.desktop.wm.preferences button-layout

# Tiling: no gaps between windows, no snap assistant
layout-tiling-dewy:
    gsettings set org.gnome.shell.extensions.tilingshell show-indicator true
    gsettings set org.gnome.shell.extensions.tilingshell inner-gaps 0
    gsettings set org.gnome.shell.extensions.tilingshell outer-gaps 0
    gsettings set org.gnome.shell.extensions.tilingshell enable-snap-assist false
    gsettings set org.gnome.shell.extensions.tilingshell focus-window-up "['']"
    gsettings set org.gnome.shell.extensions.tilingshell focus-window-down "['']"
    gsettings set org.gnome.shell.extensions.tilingshell focus-window-left "['']"
    gsettings set org.gnome.shell.extensions.tilingshell focus-window-right "['']"
    gsettings set org.gnome.shell.extensions.tilingshell move-window-up "['<Super>Up']"
    gsettings set org.gnome.shell.extensions.tilingshell move-window-down "['<Super>Down']"
    gsettings set org.gnome.shell.extensions.tilingshell move-window-left "['<Super>Left']"
    gsettings set org.gnome.shell.extensions.tilingshell move-window-right "['<Super>Right']"
    gsettings set org.gnome.shell.extensions.tilingshell cycle-layouts "['<Control>Right']"

# Tiling: back to the default gaps, snap assistant and shortcuts
layout-tiling-default:
    gsettings reset org.gnome.shell.extensions.tilingshell show-indicator
    gsettings reset org.gnome.shell.extensions.tilingshell inner-gaps
    gsettings reset org.gnome.shell.extensions.tilingshell outer-gaps
    gsettings reset org.gnome.shell.extensions.tilingshell enable-snap-assist
    gsettings reset org.gnome.shell.extensions.tilingshell focus-window-up
    gsettings reset org.gnome.shell.extensions.tilingshell focus-window-down
    gsettings reset org.gnome.shell.extensions.tilingshell focus-window-left
    gsettings reset org.gnome.shell.extensions.tilingshell focus-window-right
    gsettings reset org.gnome.shell.extensions.tilingshell move-window-up
    gsettings reset org.gnome.shell.extensions.tilingshell move-window-down
    gsettings reset org.gnome.shell.extensions.tilingshell move-window-left
    gsettings reset org.gnome.shell.extensions.tilingshell move-window-right
    gsettings reset org.gnome.shell.extensions.tilingshell cycle-layouts

# App grid order and folders are separate choices.
# The grid is alphabetical by default (Alphabetical App Grid, on in the image's
# default extensions), with GNOME's folders. These recipes change one or the other.

# Keep the app grid alphabetical, and show dock apps in it too
sort-app-grid:
    # A one-time sort now, so it looks right before the extension loads.
    gsettings reset org.gnome.shell app-picker-layout
    # Alphabetical App Grid keeps it sorted, apps installed later included.
    gnome-extensions enable AlphabeticalAppGrid@stuarthayhurst
    # Pinned Apps in App Grid keeps dock apps in the grid as well.
    gnome-extensions enable pinned-apps-in-appgrid@brunosilva.io

# GNOME's own app grid order: new apps go at the end, and icons can be arranged by hand
default-app-grid:
    gnome-extensions disable AlphabeticalAppGrid@stuarthayhurst || true
    gnome-extensions disable pinned-apps-in-appgrid@brunosilva.io || true
    gsettings reset org.gnome.shell app-picker-layout

# Put every app in the main grid, with no folders
flatten-app-folders:
    gsettings set org.gnome.desktop.app-folders folder-children "[]"

# Bring back the default app folders
default-app-folders:
    gsettings reset org.gnome.desktop.app-folders folder-children

# --- LAYOUT PRESETS ---
# Each preset applies live through `redfox-layout` (see `redfox-layout list`);
# no logout needed. Switching presets resets the dock/panel settings first.

# Layout preset: RedFox (floating dock on big screens, GNOME dash on small ones)
preset-dock-redfox GAP="8":
    redfox-layout set redfox
    gsettings set org.gnome.shell.extensions.redfox-layouts floating-dock-gap {{ GAP }}

# Layout preset: GNOME (no dock; the dash lives in the overview)
preset-dock-gnome:
    redfox-layout set gnome

# Layout preset: Ubuntu (full-height dock on the left)
preset-dock-ubuntu:
    redfox-layout set ubuntu

# Layout preset: Cal (floating dock along the bottom, window buttons on the left)
preset-dock-cal GAP="8":
    redfox-layout set cal
    gsettings set org.gnome.shell.extensions.redfox-layouts floating-dock-gap {{ GAP }}

# Layout preset: Wash (one taskbar along the bottom, start menu and apps centred)
preset-dock-wash:
    redfox-layout set wash

# Layout preset: Nostalgia (one taskbar along the bottom, start menu and apps on the left)
preset-dock-nostalgia:
    redfox-layout set nostalgia

# Hardware Atoms
fix-oryp9-mouse:
    #!/usr/bin/bash
    RULE_PATH="/etc/udev/rules.d/99-block-ghost-mouse.rules"
    RULE_CONTENT='ACTION=="add|change", KERNEL=="event*", ATTRS{name}=="*PS/2*Mouse", ENV{LIBINPUT_IGNORE_DEVICE}="1"'
    
    if [ -f "$RULE_PATH" ] && grep -qF "$RULE_CONTENT" "$RULE_PATH"; then
        echo "[OK] udev rule already exists. No action needed."
        exit 0
    fi

    echo "Applying udev rule to ignore ghost PS/2 mouse..."
    echo "$RULE_CONTENT" | sudo tee "$RULE_PATH" > /dev/null
    echo "Reloading udev rules..."
    sudo udevadm control --reload-rules && sudo udevadm trigger
    echo "Done."

fix-acer-nouveau:
    #!/usr/bin/bash
    set -euo pipefail
    
    echo "Gathering NVIDIA PCI IDs..."
    # Extracts the PCI IDs for the Nvidia GPU and its Audio component (e.g., 10de:1c8c,10de:0fb9)
    NV_IDS=$(lspci -nn | grep -i NVIDIA | grep -o '\[10de:[0-9a-fA-F]*\]' | tr -d '[]' | paste -sd "," -)
    
    if [ -z "$NV_IDS" ]; then
        echo "No NVIDIA devices found. Skipping."
        exit 0
    fi
    
    echo "Found NVIDIA devices: $NV_IDS"
    
    # Check if kargs are already set to avoid triggering an ostree deployment loop
    KARGS=$(rpm-ostree kargs)
    if ! grep -q "vfio-pci.ids=$NV_IDS" <<< "$KARGS" || ! grep -q "module_blacklist=nouveau,nvidia" <<< "$KARGS"; then
        echo "Binding dead dGPU to vfio-pci to force D3 sleep state..."
        
        # 1. rd.driver.pre=vfio-pci : Loads the stub driver into the initramfs before anything else.
        # 2. vfio-pci.ids=... : Tells the stub driver to permanently claim your specific Acer GPU.
        # 3. module_blacklist : Failsafe to ensure nouveau/nvidia don't race the stub driver and hit the bad VRAM.
        #    It's a single parameter (a repeated one overrides the earlier value), so both go in one list;
        #    the old split form is removed if present.
        sudo rpm-ostree kargs \
            --delete-if-present="module_blacklist=nouveau" \
            --delete-if-present="module_blacklist=nvidia" \
            --append-if-missing="rd.driver.pre=vfio-pci" \
            --append-if-missing="vfio-pci.ids=$NV_IDS" \
            --append-if-missing="module_blacklist=nouveau,nvidia"
            
        echo "Success! The dead dGPU will be permanently isolated and put to sleep on the next reboot."
    else
        echo "The Acer dGPU is already quarantined. No action needed."
    fi

# Apply this machine's hardware quirk recipes from config.yaml (machines.<id>.quirks)
apply-hardware-quirks:
    #!/usr/bin/bash
    set -euo pipefail
    LOG_FILE="${XDG_RUNTIME_DIR:-$HOME/.cache}/redfox-bootstrap-current.log"
    if ! /usr/bin/redfox-config get machines &>/dev/null; then
        if /usr/bin/redfox-config get hardware.quirks &>/dev/null; then
            echo "[WARN] config.yaml uses the old 'hardware.quirks' format; move entries under 'machines:'."
            echo "- Hardware quirks skipped (config.yaml uses old hardware.quirks format; move to machines:)" >> "$LOG_FILE"
        else
            echo "No machines configured in config.yaml. Skipping hardware quirks."
        fi
        exit 0
    fi
    SERIAL=$(sudo cat /sys/class/dmi/id/product_serial 2>/dev/null || true)
    mapfile -t QUIRKS < <(/usr/bin/redfox-config machine quirks --id "$SERIAL" 2>/dev/null || true)
    if [ ${#QUIRKS[@]} -eq 0 ]; then
        echo "No hardware quirks mapped for this device."
        exit 0
    fi
    for QUIRK in "${QUIRKS[@]}"; do
        if [[ ! "$QUIRK" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
            echo "[WARN] Ignoring invalid quirk recipe name: '$QUIRK'"
            echo "- Hardware quirk '$QUIRK' ignored (not a valid recipe name)" >> "$LOG_FILE"
            continue
        fi
        echo "Hardware match found! Applying quirk: $QUIRK"
        if ! just "$QUIRK"; then
            echo "- Hardware quirk '$QUIRK' failed (retry with: ujust $QUIRK)" >> "$LOG_FILE"
        fi
    done

# Configure NordVPN silently from config.yaml (never aborts a bootstrap; problems go to the recap)
configure-nordvpn:
    #!/usr/bin/bash
    LOG_FILE="${XDG_RUNTIME_DIR:-$HOME/.cache}/redfox-bootstrap-current.log"
    if ! /usr/bin/redfox-config get nordvpn.token &>/dev/null; then
        echo "No NordVPN token in ~/.config/redfox/config.yaml. Skipping NordVPN setup."
        echo "- NordVPN skipped (no nordvpn.token in config.yaml)" >> "$LOG_FILE"
        exit 0
    fi
    echo "Configuring NordVPN WireGuard connections..."
    if ! /usr/bin/redfox-nord sync; then
        echo "[WARN] NordVPN setup did not fully complete (see output above)."
        echo "- NordVPN setup incomplete (see output above; retry with: ujust nord-sync)" >> "$LOG_FILE"
    fi

# Delete all RedFox-managed NordVPN connections (other VPNs are left alone)
nuke-vpns:
    @echo "WARNING: This will permanently delete all RedFox NordVPN connections."
    /usr/bin/redfox-nord nuke -y

# Synchronize NordVPN WireGuard fleet against active profile
nord-sync:
    /usr/bin/redfox-nord sync

# List installed NordVPN connections
nord-list:
    /usr/bin/redfox-nord list

# Add a NordVPN connection (e.g. ujust nord-add US --p2p)
[positional-arguments]
nord-add *args:
    /usr/bin/redfox-nord add "$@"

# Remove NordVPN connection(s) (e.g. ujust nord-remove US, ujust nord-remove "NordVPN US #13024")
[positional-arguments]
nord-remove *args:
    /usr/bin/redfox-nord remove "$@"

# Enable weekly ClamAV antivirus scans (and the signature updater they rely on)
enable-clamav-weekly:
    sudo systemctl enable --now clamav-freshclam.service clamscan-weekly.timer
    systemctl list-timers clamscan-weekly.timer

# Disable weekly ClamAV antivirus scans and signature updates
disable-clamav-weekly:
    sudo systemctl disable --now clamscan-weekly.timer clamav-freshclam.service

# Create and enable a swapfile (Default: 16G)
add-swap size="16G":
    #!/usr/bin/bash
    set -euo pipefail
    
    # Calculate exact bytes requested (e.g., 16G = 17179869184); accepts 16g, 16G, 16GiB, 16GB
    SIZE=$(echo "{{size}}" | tr '[:lower:]' '[:upper:]' | sed -E 's/I?B$//')
    REQ_BYTES=$(numfmt --from=iec "$SIZE")
    
    is_active() { swapon --show=NAME --noheadings | grep -qx "/var/swapfile"; }

    if [ -f /var/swapfile ]; then
        CUR_BYTES=$(stat -c "%s" /var/swapfile 2>/dev/null || echo "0")
        if [ "$CUR_BYTES" != "$REQ_BYTES" ]; then
            echo "Swap size mismatch. Resizing to {{size}}..."
            sudo swapoff /var/swapfile 2>/dev/null || true
            sudo rm -f /var/swapfile
        elif is_active; then
            echo "[OK] Swapfile already active at requested size ({{size}})."
        else
            # Left behind by an interrupted run or a manual swapoff: reuse it, or recreate if unusable
            echo "Found inactive swapfile at requested size. Activating..."
            if ! sudo swapon /var/swapfile; then
                echo "Existing swapfile is unusable. Recreating..."
                sudo rm -f /var/swapfile
            fi
        fi
    fi

    if [ ! -f /var/swapfile ]; then
        echo "Creating {{size}} swapfile in /var/swapfile..."
        # We use the native btrfs command to safely handle Copy-On-Write (NOCOW) requirements
        sudo btrfs filesystem mkswapfile --size "$SIZE" /var/swapfile
        sudo swapon /var/swapfile
    fi
    
    echo "Ensuring swap is persistent in /etc/fstab..."
    if ! grep -q '^/var/swapfile' /etc/fstab; then
        echo "/var/swapfile none swap defaults 0 0" | sudo tee -a /etc/fstab
    fi
    echo "[SUCCESS] Swapfile enabled!"

# Disable and remove the swapfile
remove-swap:
    #!/usr/bin/bash
    set -euo pipefail
    if [ ! -f /var/swapfile ] && ! grep -q '^/var/swapfile' /etc/fstab; then
        echo "[OK] No swapfile found at /var/swapfile and none in fstab. Nothing to do."
        exit 0
    fi

    echo "Disabling swapfile..."
    sudo swapoff /var/swapfile || true
    
    echo "Removing from /etc/fstab..."
    sudo sed -i '/^\/var\/swapfile/d' /etc/fstab
    
    if [ -f /var/swapfile ]; then
        echo "Deleting the swapfile..."
        sudo rm -f /var/swapfile
    fi
    echo "Swapfile successfully removed!"


# Level 1.5: Small-ecules (Software packs)
# The lists live in /usr/share/redfox/software.yaml; `redfox-software list` shows them.

# Install Basic Apps
install-basic:
    /usr/bin/redfox-software install basic

# Install Productivity Apps
install-productivity:
    /usr/bin/redfox-software install productivity
# Consider OnlyOffice for PDF capabilities

# Install Communication Apps
install-comms:
    /usr/bin/redfox-software install comms

# Install Daily Apps
install-daily:
    /usr/bin/redfox-software install daily

# Install Audio Production Apps
install-audio:
    /usr/bin/redfox-software install audio
# Consider FamiStudio

# Install Graphics Apps
install-graphics:
    /usr/bin/redfox-software install graphics

# Install Photography Apps
install-photos:
    /usr/bin/redfox-software install photos

# Install Video Production Apps
install-video:
    /usr/bin/redfox-software install video

# Install Compatibility Tools
install-compatibility:
    /usr/bin/redfox-software install compatibility

# Install Music Notation Apps
install-notation:
    /usr/bin/redfox-software install notation

# Install Writing Apps
install-writing:
    /usr/bin/redfox-software install writing

# Install GNOME Development Apps
install-gnome-dev:
    /usr/bin/redfox-software install gnome-dev

# Install Development Apps
install-dev:
    /usr/bin/redfox-software install dev

# Install Bluefin DX Extras
install-bluefin-dx:
    /usr/bin/redfox-software install bluefin-dx

# Install Creative Suite
install-creative:
    /usr/bin/redfox-software install creative


# Level 2: Molecules (Logical Groups)

# Install Matt's Bundle
install-matt:
    /usr/bin/redfox-software install matt

# Install Dewy's Bundle
install-dewy:
    /usr/bin/redfox-software install dewy

# Install Normie Bundle
install-normie:
    /usr/bin/redfox-software install normie


# Level 3: Organisms (User Bootstraps & Configs)

# --- CONFIG MOLECULES (User/Tool Setup) ---

# Reset Keybindings to Default
configure-keybindings-default:
    gsettings reset-recursively org.gnome.shell.keybindings

# Enable Tilix as the default terminal (Shortcuts + Context Menu)
configure-terminal-tilix:
    @echo "Activating Tilix integration..."
    # 1. Configure the extension to use Tilix
    gsettings set com.github.stunkymonkey.nautilus-open-any-terminal terminal tilix
    gsettings set com.github.stunkymonkey.nautilus-open-any-terminal keybindings '<Ctrl><Alt>t'
    gsettings set com.github.stunkymonkey.nautilus-open-any-terminal new-tab true
    
    # 2. Set the GNOME global shortcut (<Ctrl><Alt>T)
    # We use a custom keybinding slot to override the default Ptyxis behavior reliably.
    dconf write /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/name "'Tilix'"
    dconf write /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/command "'tilix'"
    dconf write /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/binding "'<Control><Alt>t'"
    # Add custom0 to the keybinding list without dropping other entries (e.g. Midikeep shortcuts)
    python3 -c 'import ast, subprocess as sp; key = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"; slot = key + "/custom0/"; out = sp.check_output(["dconf", "read", key], text=True).strip(); b = ast.literal_eval(out.removeprefix("@as ")) if out else []; b = b if slot in b else b + [slot]; sp.run(["dconf", "write", key, "@as " + repr(b)], check=True)'
    
    # 3. Reload Nautilus to pick up the extension config
    nautilus -q || true    
    @echo "Done. Tilix is now the default."

# Restore the default terminal (Ptyxis)
configure-terminal-default:
    @echo "Restoring system default terminal (Ptyxis)..."
    # 1. Reset the extension to defaults (it defaults to 'kgx' or 'gnome-terminal')
    gsettings reset com.github.stunkymonkey.nautilus-open-any-terminal terminal
    gsettings reset com.github.stunkymonkey.nautilus-open-any-terminal keybindings
    
    # 2. Clear the custom shortcut so the system default (Ptyxis) takes over
    dconf reset /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/name
    dconf reset /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/command
    dconf reset /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/binding
    # Remove only custom0 from the keybinding list (other entries, e.g. Midikeep shortcuts, stay)
    python3 -c 'import ast, subprocess as sp; key = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"; slot = key + "/custom0/"; out = sp.check_output(["dconf", "read", key], text=True).strip(); b = ast.literal_eval(out.removeprefix("@as ")) if out else []; sp.run(["dconf", "write", key, "@as " + repr([x for x in b if x != slot])], check=True)'
    
    # 3. Reload Nautilus
    nautilus -q || true
    @echo "Done. Restored to Ptyxis."

# Configure Power Saver, Suspend (default)
configure-powersaver-default:
    gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'suspend'

# Configure Power Saver, No Suspend (tweak)
configure-powersaver-no-suspend:
    gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'

# Disable xwayland-native-scaling (Reset)
configure-xway-scale-off:
    gsettings reset org.gnome.mutter.wayland xwayland-scaling-factor
    echo "Disabled xwayland-native-scaling (reverted factor to default)"

# Enable xwayland-native-scaling (Deviation)
configure-xway-scale-on:
    gsettings set org.gnome.mutter.wayland xwayland-scaling-factor 0.0
    echo "Enabled xwayland-native-scaling (forced factor to 0.0)"

# Enable Midikeep (background MIDI recording service + global key shortcuts)
enable-midikeep: start-midikeep-service configure-midikeep-shortcuts
    echo "Midikeep enabled."

# Disable Midikeep (stop background MIDI recording service + remove global key shortcuts)
disable-midikeep: stop-midikeep-service remove-midikeep-shortcuts
    echo "Midikeep disabled."

# Start Midikeep background MIDI recording service
start-midikeep-service:
    systemctl --user enable --now midikeep.service
    echo "Midikeep service enabled and started."

# Stop Midikeep background MIDI recording service
stop-midikeep-service:
    systemctl --user disable --now midikeep.service
    echo "Midikeep service disabled and stopped."

# Mark active Midikeep take with a Clapper flag (★)
mark-midikeep:
    /usr/bin/midikeep mark

# Prompt for comment and mark active Midikeep take (<Ctrl><Alt><Super>m)
comment-midikeep:
    /usr/bin/midikeep mark --interactive

# Restart Midikeep session / finalize current take immediately
restart-midikeep:
    /usr/bin/midikeep restart

# Configure Midikeep global key shortcuts (<Ctrl><Alt><Super>k, <Ctrl><Alt><Super>r, and <Ctrl><Alt><Super>m)
configure-midikeep-shortcuts:
    #!/usr/bin/python3
    import subprocess
    import ast

    def set_slot(slot, name, cmd, binding):
        base = f"/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/{slot}/"
        subprocess.run(["dconf", "write", f"{base}name", f"'{name}'"])
        subprocess.run(["dconf", "write", f"{base}command", f"'{cmd}'"])
        subprocess.run(["dconf", "write", f"{base}binding", f"'{binding}'"])
        return base

    out = subprocess.check_output(
        ["gsettings", "get", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings"],
        text=True,
    ).strip()
    bindings = ast.literal_eval(out) if out.startswith("[") else []

    p1 = set_slot("midikeep-mark", "Midikeep Mark Take (Clapper)", "/usr/bin/midikeep mark", "<Control><Alt><Super>k")
    p2 = set_slot("midikeep-restart", "Midikeep Restart Take", "/usr/bin/midikeep restart", "<Control><Alt><Super>r")
    p3 = set_slot("midikeep-comment", "Midikeep Mark Take with Comment", "/usr/bin/midikeep mark --interactive", "<Control><Alt><Super>m")

    for p in [p1, p2, p3]:
        if p not in bindings:
            bindings.append(p)

    val = "[" + ", ".join(f"'{b}'" for b in bindings) + "]"
    subprocess.run(["dconf", "write", "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings", val])
    print("Configured Midikeep shortcuts: <Control><Alt><Super>k (Clapper), <Control><Alt><Super>r (Restart), <Control><Alt><Super>m (Comment)")

# Remove Midikeep global key shortcuts
remove-midikeep-shortcuts:
    #!/usr/bin/python3
    import subprocess
    import ast

    base = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"
    slots = [f"{base}/{slot}/" for slot in ["midikeep-mark", "midikeep-restart", "midikeep-comment"]]

    out = subprocess.check_output(
        ["gsettings", "get", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings"],
        text=True,
    ).strip()
    bindings = ast.literal_eval(out) if out.startswith("[") else []
    bindings = [b for b in bindings if b not in slots]

    val = "@as [" + ", ".join(f"'{b}'" for b in bindings) + "]"
    subprocess.run(["dconf", "write", base, val])
    for slot in slots:
        subprocess.run(["dconf", "reset", "-f", slot])
    print("Removed Midikeep shortcuts.")

# Configure Music Production / Audio Workstation
configure-music: enable-midikeep
    echo "Configured music workstation."

# Configure Dev Environment
configure-dev: configure-vscode configure-cursor

# Configure Matt's Environment
configure-matt: redfox-enforce-config apply-hardware-quirks add-swap configure-nordvpn reset-hostname configure-keybindings-default configure-dev configure-text-editor-dev configure-terminal-default configure-powersaver-no-suspend configure-xway-scale-off configure-music configure-autostart-tray
    mkdir -p ~/dev
    gnome-extensions enable unblank@sun.wxg@gmail.com
    # just runs hardware atoms here eventually
    # e.g., fix-oryp9-mouse

# Configure Cursor for Dewy
configure-cursor-dewy:
    #!/usr/bin/bash
    echo "Configuring Cursor for Dewy..."
    cursor --install-extension charliermarsh.ruff --force
    
    SETTINGS_FILE="$HOME/.config/Cursor/User/settings.json"
    mkdir -p "$(dirname "$SETTINGS_FILE")"
    
    if [ ! -f "$SETTINGS_FILE" ]; then
        echo "{}" > "$SETTINGS_FILE"
    fi

    # Use the RedFox helper script to patch settings
    /usr/bin/redfox-patch-json "$SETTINGS_FILE" "workbench.colorTheme" "Default Dark Modern"
    
    echo "Cursor configured successfully!"

# VLC's speed keys the way Dewy likes them, like the browser's video speed
# controller: S and D step the speed down and up by 0.1 (VLC's fine speed
# keys, [ and ] still work too), R back to normal speed (= still works).
# Frees S (Stop; the Media Stop key still stops), D (deinterlace) and R
# (random). Quit VLC first: it rewrites its settings when it closes.
configure-vlc-dewy:
    #!/usr/bin/bash
    set -euo pipefail
    echo "Setting VLC's speed keys (S slower, D faster, R normal speed)..."
    tab=$'\t'
    keys=(
        "key-rate-slower-fine=s${tab}["
        "key-rate-faster-fine=d${tab}]"
        "key-rate-normal=r${tab}="
        "key-stop=Media Stop"
        "key-deinterlace="
        "key-random="
    )
    # The Flatpak's settings, and the native VLC's if it's ever used.
    for rc in "$HOME/.var/app/org.videolan.VLC/config/vlc/vlcrc" "$HOME/.config/vlc/vlcrc"; do
        case "$rc" in
            "$HOME/.config/"*) command -v vlc >/dev/null || [ -e "$rc" ] || continue ;;
        esac
        mkdir -p "$(dirname "$rc")"
        [ -e "$rc" ] || printf '[core] # core program\n' > "$rc"
        grep -q '^\[core\]' "$rc" || printf '\n[core] # core program\n' >> "$rc"
        for kv in "${keys[@]}"; do
            name=${kv%%=*}
            # Drop the option wherever it is (set or commented out), then
            # set it at the top of [core].
            awk -v n="$name" -v kv="$kv" '
                $0 ~ "^#?" n "=" { next }
                { print }
                /^\[core\]/ { print kv }
            ' "$rc" > "$rc.new"
            mv -- "$rc.new" "$rc"
        done
        echo "  $rc"
    done
    if pgrep -x vlc >/dev/null; then
        echo "VLC is open: quit it and run this again, or it may put the old keys back."
    fi
    echo "Done. In VLC: S slower, D faster (0.1 steps), R normal speed."

# Configure Dewy's Environment
configure-dewy: redfox-enforce-config configure-keybindings-default configure-text-editor-dev reset-hostname configure-cursor-dewy configure-terminal-tilix configure-vlc-dewy configure-nordvpn configure-powersaver-default configure-xway-scale-on enable-clamav-weekly
    gsettings set org.gnome.shell.keybindings show-screenshot-ui "['Print']"
    gsettings set org.gnome.shell.keybindings screenshot "['<Shift><Super>s']"
    gnome-extensions disable unblank@sun.wxg@gmail.com
    gnome-extensions enable redfox-dim@redfoxlabs.tech

# Configure Fedora's Environment
configure-fedora: configure-keybindings-default configure-text-editor-reset reset-hostname configure-powersaver-default configure-xway-scale-on
    gnome-extensions disable unblank@sun.wxg@gmail.com

# Configure Normie's Environment
configure-normie: configure-keybindings-default configure-text-editor-reset reset-hostname configure-powersaver-no-suspend configure-xway-scale-off
    gnome-extensions enable unblank@sun.wxg@gmail.com


# --- LAYOUT MOLECULES (UX/Behavior/Positioning) ---

# Layout Matt
layout-matt: sort-app-grid flatten-app-folders layout-tiling-default preset-dock-gnome set-window-controls-left-gnome
    gsettings reset-recursively org.gnome.shell.extensions.dash-to-dock
    gsettings set org.gnome.shell favorite-apps "[\
      'org.gnome.Ptyxis.desktop', \
      'org.gnome.Nautilus.desktop', \
      'com.getmailspring.Mailspring.desktop', \
      'org.mozilla.firefox.desktop', \
      'org.signal.Signal.desktop', \
      'org.gnome.TextEditor.desktop', \
      'com.spotify.Client.desktop', \
      'steam.desktop', \
      'net.cozic.joplin_desktop.desktop', \
      'io.github.kolunmi.Bazaar.desktop', \
      'org.gnome.Settings.desktop']"
    # Note: Add Gemini Web App ID and Dorico 6 once stabilized.

# Layout Dewy
layout-dewy: sort-app-grid flatten-app-folders layout-tiling-dewy preset-dock-ubuntu set-window-controls-right-full
    gsettings set org.gnome.shell.extensions.dash-to-dock isolate-workspaces true
    gsettings set org.gnome.shell.extensions.dash-to-dock dash-max-icon-size 40
    gsettings set org.gnome.shell favorite-apps "['org.gnome.Nautilus.desktop', 'net.nokyan.Resources.desktop', 'org.gnome.Settings.desktop', 'org.gnome.Ptyxis.desktop', 'org.mozilla.firefox.desktop', 'com.brave.Browser.desktop', 'org.gnome.Calculator.desktop', 'org.gnome.TextEditor.desktop', 'dev.zed.Zed.desktop', 'cursor.desktop', 'com.spotify.Client.desktop', 'com.slack.Slack.desktop', 'org.signal.Signal.desktop', 'dev.vencord.Vesktop.desktop']"

# Layout Fedora (Mostly Vanilla Fedora 43 Defaults)
layout-fedora: default-app-grid default-app-folders layout-tiling-default preset-dock-gnome set-window-controls-right-gnome
    gsettings reset-recursively org.gnome.shell.extensions.dash-to-dock
    gsettings set org.gnome.shell favorite-apps "['org.mozilla.firefox.desktop', 'org.gnome.Calendar.desktop', 'org.gnome.Nautilus.desktop', 'io.github.kolunmi.Bazaar.desktop', 'org.gnome.TextEditor.desktop', 'org.gnome.Calculator.desktop']"

# Layout Normie (Consumer-focused Experience)
layout-normie: sort-app-grid default-app-folders set-window-controls-left-gnome layout-tiling-default
    gsettings set org.gnome.shell favorite-apps "[\
      'org.gnome.Nautilus.desktop', \
      'com.getmailspring.Mailspring.desktop', \
      'org.mozilla.firefox.desktop', \
      'org.signal.Signal.desktop', \
      'org.gnome.Calendar.desktop', \
      'org.libreoffice.LibreOffice.writer.desktop', \
      'com.spotify.Client.desktop', \
      'net.cozic.joplin_desktop.desktop', \
      'steam.desktop', \
      'io.gitlab.news_flash.NewsFlash.desktop', \
      'dev.geopjr.Tuba.desktop', \
      'app.drey.Warp.desktop', \
      'io.github.kolunmi.Bazaar.desktop', \
      'org.gnome.Settings.desktop', \
      'tech.redfoxlabs.Hub.desktop']"

# --- THEME MOLECULES (Visuals/Assets) ---

# Theme Matt
theme-matt: theme-text-editor-default theme-sound-fedora theme-default-corners
    echo "Applying Matt's Visual Theme..."
    # gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita-dark'
    # gsettings set org.gnome.desktop.background picture-uri 'file:///...'

# Theme Dewy
theme-dewy: theme-text-editor-dewy theme-square-corners
    echo "Applying Dewy's Visual Theme..."
    # gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita'
    # theme-sound-bazzite

# Theme Fedora
theme-fedora: theme-text-editor-default theme-sound-fedora theme-default-corners

# Theme Normie
theme-normie: theme-text-editor-default theme-sound-fedora theme-default-corners


# --- BOOTSTRAP ORGANISMS ---

# Bootstrap Matt
bootstrap-matt: _reset-bootstrap-recap configure-matt install-matt theme-matt layout-matt _print-bootstrap-recap
# Bootstrap Dewy
bootstrap-dewy: _reset-bootstrap-recap configure-dewy install-dewy theme-dewy layout-dewy _print-bootstrap-recap

# Bootstrap Fedora
bootstrap-fedora: _reset-bootstrap-recap theme-fedora layout-fedora configure-fedora _print-bootstrap-recap

# Bootstrap Normie
bootstrap-normie: _reset-bootstrap-recap install-normie theme-normie layout-normie configure-normie _print-bootstrap-recap

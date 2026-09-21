# Level 1: Atoms (Single-Purpose Scripts)

# Setup System Configuration (The "Front Desk" Pattern)
# This recipe is the first dependency for any recipe chain requiring private configuration or hardware quirks.
# Ensures ~/.config/redfox/config.yaml is present. Headless-safe: skips gracefully with recap ledger.
redfox-enforce-config:
    #!/usr/bin/bash
    set -euo pipefail
    CONFIG_FILE="$HOME/.config/redfox/config.yaml"
    LOG_FILE="/tmp/redfox-bootstrap-current.log"

    if [ -s "$CONFIG_FILE" ]; then
        exit 0
    fi

    if [ ! -t 0 ]; then
        echo "- System configuration skipped (Headless mode, using defaults)" >> "$LOG_FILE"
        exit 0
    fi

    # Interactive prompt via redfox-config setup
    /usr/bin/redfox-config setup || true

# Backwards-compatible alias for existing scripts/habits
redfox-enforce-secrets: redfox-enforce-config

# Interactively setup or update configuration (paste, file, or URL)
redfox-setup-config:
    /usr/bin/redfox-config setup

# Edit configuration file in text editor
redfox-edit-config:
    /usr/bin/redfox-config edit

# Backwards-compatible aliases
redfox-update-secrets: redfox-edit-config
redfox-init-secrets: redfox-setup-config

# Evaluates the run and archives the ledger
_print-bootstrap-recap:
    #!/usr/bin/bash
    LOG_FILE="/tmp/redfox-bootstrap-current.log"
    ARCHIVE_DIR="$HOME/.local/state/redfox"
    
    echo ""
    echo "================================================================="
    if [ -f "$LOG_FILE" ]; then
        echo " ⚠️  Bootstrap Complete (With Skipped Items)"
        echo "================================================================="
        cat "$LOG_FILE"
        echo "-----------------------------------------------------------------"
        echo " You can configure these later by running: just redfox-edit-config"
        
        mkdir -p "$ARCHIVE_DIR"
        mv "$LOG_FILE" "$ARCHIVE_DIR/bootstrap-$(date +%Y%m%d-%H%M%S).log"
    else
        echo " 🎉 Bootstrap Complete! All systems go."
        echo "================================================================="
    fi

# Permanently delete all saved configuration files
redfox-reset-config:
    /usr/bin/redfox-config reset

# Backwards-compatible alias
redfox-reset-secrets: redfox-reset-config

# Reset hostname to "redfox" (from whatever was inherited from upstream, likely "bazzite")
reset-hostname:
    @echo "Setting hostname to redfox..."
    hostnamectl set-hostname redfox
    hostnamectl set-hostname --pretty "RedFoxOS"
    @echo "Done! Please reboot for all changes to take full effect."

# Configure Git
configure-git:
    echo "TODO: Implement configure-git"

# Configure VSCode
configure-vscode:
    echo "TODO: Implement configure-vscode"

# Configure Cursor
configure-cursor:
    echo "TODO: Implement configure-cursor"

# Configure Antigravity IDE
configure-antigravity:
    echo "TODO: Implement configure-antigravity"

# Configure Text Editor Dev Mode (Indentation)
configure-text-editor-dev:
    echo "Configuring Text Editor for Development (Spaces, 4 per tab)..."
    flatpak run --command=gsettings org.gnome.TextEditor set org.gnome.TextEditor indent-style 'space'
    flatpak run --command=gsettings org.gnome.TextEditor set org.gnome.TextEditor tab-width 4
    flatpak run --command=gsettings org.gnome.TextEditor set org.gnome.TextEditor restore-session false

# Reset Text Editor Configuration (Indentation)
configure-text-editor-reset:
    echo "Resetting Text Editor indentation to defaults..."
    flatpak run --command=gsettings org.gnome.TextEditor reset org.gnome.TextEditor indent-style
    flatpak run --command=gsettings org.gnome.TextEditor reset org.gnome.TextEditor tab-width
    flatpak run --command=gsettings org.gnome.TextEditor reset org.gnome.TextEditor restore-session

# Theme Text Editor Dewy (Visuals)
theme-text-editor-dewy:
    echo "Configuring Text Editor Visuals (Dark Mode, Line Numbers, Map, Highlight)..."
    flatpak run --command=gsettings org.gnome.TextEditor set org.gnome.TextEditor style-variant 'dark'
    flatpak run --command=gsettings org.gnome.TextEditor set org.gnome.TextEditor show-line-numbers true
    flatpak run --command=gsettings org.gnome.TextEditor set org.gnome.TextEditor show-map true
    flatpak run --command=gsettings org.gnome.TextEditor set org.gnome.TextEditor highlight-current-line true

# Theme Text Editor Default (Visuals Reset)
theme-text-editor-default:
    echo "Resetting Text Editor visuals to defaults..."
    flatpak run --command=gsettings org.gnome.TextEditor reset org.gnome.TextEditor style-variant
    flatpak run --command=gsettings org.gnome.TextEditor reset org.gnome.TextEditor show-line-numbers
    flatpak run --command=gsettings org.gnome.TextEditor reset org.gnome.TextEditor show-map
    flatpak run --command=gsettings org.gnome.TextEditor reset org.gnome.TextEditor highlight-current-line

# Install Zed
install-zed:
    echo "Installing Zed..."
    bash -c "set -euo pipefail; curl -f https://zed.dev/install.sh | sh"
    echo "Zed installed!"

# Uninstall Zed
uninstall-zed:
    echo "Uninstalling Zed..."
    if command -v zed &> /dev/null; then \
        zed --uninstall; \
    elif [ -x "$HOME/.local/bin/zed" ]; then \
        "$HOME/.local/bin/zed" --uninstall; \
    else \
        echo "Zed executable not found."; \
    fi
    if ! command -v zed &> /dev/null && [ ! -x "$HOME/.local/bin/zed" ]; then \
        echo "Zed uninstalled successfully!"; \
    else \
        echo "Zed was not removed (possibly cancelled or error)."; \
    fi


# Install Antigravity CLI
install-antigravity-cli:
    echo "Installing Antigravity CLI..."
    curl -fsSL https://antigravity.google/cli/install.sh | bash
    echo "Antigravity CLI installed!"

# Uninstall Antigravity CLI
uninstall-antigravity-cli:
    echo "Uninstalling Antigravity CLI..."
    rm -rf ~/.local/bin/antigravity
    echo "Antigravity CLI uninstalled!"

# Configure Heroic
configure-heroic:
    echo "TODO: Implement configure-heroic"

# Install SoundThread
install-soundthread:
    /usr/bin/update-soundthread

# Uninstall SoundThread
uninstall-soundthread:
    /usr/bin/uninstall-soundthread

# Run complete system, Flatpak, Brew, and application updates via Topgrade
[group("system")]
update:
    #!/usr/bin/bash
    if [[ -t 0 && -t 1 ]]; then
        /usr/bin/topgrade --config /usr/share/ublue-os/topgrade.toml --keep
    else
        /usr/bin/topgrade --config /usr/share/ublue-os/topgrade.toml
    fi

# Run the optional Bazzite graphical updater
update-gui:
    #!/usr/bin/bash
    bazzite-updater >/dev/null 2>&1 &

# Update all AppImages managed by Gearlever
update-appimages:
    /usr/bin/update-appimages

# Install Winboat (Example: GitHub Source)
install-winboat:
    /usr/bin/install-appimage \
      "WinBoat" \
      "GithubUpdater" \
      "https://github.com/TibixDev/winboat" \
      "winboat-*-x86_64.AppImage"

# Uninstall Winboat
uninstall-winboat:
    /usr/bin/uninstall-appimage "WinBoat"

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

theme-sound-fedora:
    gsettings reset org.gnome.desktop.sound theme-name

theme-sound-bazzite:
    gsettings set org.gnome.desktop.sound theme-name 'steam'

set-window-controls-right-full:
    gsettings set org.gnome.desktop.wm.preferences button-layout ':minimize,maximize,close'

set-window-controls-right-gnome:
    gsettings set org.gnome.desktop.wm.preferences button-layout ':close'

set-window-controls-left-gnome:
    gsettings reset org.gnome.desktop.wm.preferences button-layout

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

# Flatten folders, alphabetize grid, and force dock apps to show
sort-app-grid:
    # 1. Flatten folders
    # This sets the list of folders to 'empty', dumping all apps into the root grid.
    gsettings set org.gnome.desktop.app-folders folder-children "[]"
    
    # 2. Force alphabetical sort
    # This does a one-time sort immediately so it looks right even before extensions load.
    gsettings reset org.gnome.shell app-picker-layout

    # 3. Enable extensions    
    # Extension A: Alphabetical App Grid (Maintains the sort order persistently)
    gnome-extensions enable AlphabeticalAppGrid@stuarthayhurst

    # Extension B: Keep Pinned Apps (Forces dock apps back into the grid)
    gnome-extensions enable pinned-apps-in-appgrid@brunosilva.io

default-app-grid:
    echo "TODO: Implement default-app-grid"

preset-dock-ubuntu: _disable-redfox-dock-hacks
    gsettings reset-recursively org.gnome.shell.extensions.dash-to-dock
    gnome-extensions enable dash-to-dock@micxgx.gmail.com

preset-dock-gnome: _disable-redfox-dock-hacks
    gnome-extensions disable dash-to-dock@micxgx.gmail.com

preset-dock-win-classic: _disable-redfox-dock-hacks
    echo "TODO: Implement preset-dock-win-classic"

preset-dock-win-new: _disable-redfox-dock-hacks
    echo "TODO: Implement preset-dock-win-new"

preset-dock-macos: _disable-redfox-dock-hacks
    echo "TODO: Implement preset-dock-macos"

# --- REDFOX DOCK PRESET RECIPE AND UTILITIES ---

# Enable the Dash to Dock floating gap hack (Alpha) - Supports optional pixel argument
_enable-dash-to-dock-gap-hack GAP="8":
    #!/usr/bin/bash
    EXT_ID="dash-to-dock@micxgx.gmail.com"
    SYS_PATH="/usr/share/gnome-shell/extensions/${EXT_ID}"
    LOCAL_PATH="${HOME}/.local/share/gnome-shell/extensions"
    
    echo "Applying Dash to Dock gap: {{ GAP }}px"
    mkdir -p "${LOCAL_PATH}"
    rm -rf "${LOCAL_PATH}/${EXT_ID}"
    cp -r "${SYS_PATH}" "${LOCAL_PATH}/"
    
    cat << 'EOF' >> "${LOCAL_PATH}/${EXT_ID}/stylesheet.css"

    /* --- REDFOX OS CUSTOM OVERRIDES --- */
    /* 1. Zero out the internal margins to remove the 4px phantom gap */
    #dashtodockContainer #dash .dash-background {
        margin: 0px !important;
    }

    /* 2. Apply the full gap to screen edges, and 0px to the window-facing edge */
    #dashtodockContainer.bottom #dash { margin: 0px {{ GAP }}px {{ GAP }}px {{ GAP }}px !important; }
    #dashtodockContainer.top #dash { margin: {{ GAP }}px {{ GAP }}px 0px {{ GAP }}px !important; }
    #dashtodockContainer.left #dash { margin: {{ GAP }}px 0px {{ GAP }}px {{ GAP }}px !important; }
    #dashtodockContainer.right #dash { margin: {{ GAP }}px {{ GAP }}px {{ GAP }}px 0px !important; }
    EOF

# Disable the Dash to Dock floating gap hack and revert to system default
_disable-dash-to-dock-gap-hack:
    #!/usr/bin/bash
    EXT_ID="dash-to-dock@micxgx.gmail.com"
    LOCAL_PATH="${HOME}/.local/share/gnome-shell/extensions/${EXT_ID}"
    
    if [ -d "${LOCAL_PATH}" ]; then
        echo "Removing local Dash to Dock override..."
        rm -rf "${LOCAL_PATH}"
        echo "Reverted to system default. Please log out and back in."
    else
        echo "No local override found. Nothing to do."
    fi

# Fully apply RedFox Dock aesthetics (Gap Hack, Smooth Overview, Blur My Shell)
_preset-dock-redfox GAP="8": (_enable-dash-to-dock-gap-hack GAP)
    #!/usr/bin/bash
    echo "Deploying RedFox Dock Preset..."
    
    # Enable extensions
    gnome-extensions enable dash-to-dock@micxgx.gmail.com
    gnome-extensions enable smooth-overview@redfoxlabs.tech

    # Configure Blur My Shell and Dash to Dock via dconf
    dconf write /org/gnome/shell/extensions/dash-to-dock/extend-height false
    dconf write /org/gnome/shell/extensions/blur-my-shell/dash-to-dock/pipeline "'pipeline_default_rounded'"
    dconf write /org/gnome/shell/extensions/blur-my-shell/pipelines "{'pipeline_default': {'name': <'Default'>, 'effects': <[<{'type': <'native_static_gaussian_blur'>, 'id': <'effect_000000000000'>, 'params': <{'radius': <30>, 'brightness': <0.59999999999999998>}>}>]>}, 'pipeline_default_rounded': {'name': <'Default rounded'>, 'effects': <[<{'type': <'native_static_gaussian_blur'>, 'id': <'effect_000000000001'>, 'params': <{'radius': <30>, 'brightness': <0.59999999999999998>}>}>, <{'type': <'corner'>, 'id': <'effect_000000000002'>, 'params': <{'radius': <20>}>}>]>}}"

    echo "RedFox aesthetics applied. Please log out to refresh the Dash to Dock CSS."

# Disable all RedFox dock hacks and return to system defaults
_disable-redfox-dock-hacks: _disable-dash-to-dock-gap-hack
    #!/usr/bin/bash
    echo "Reverting RedFox Dock customizations..."

    # Disable Smooth Overview
    gnome-extensions disable smooth-overview@redfoxlabs.tech

    # Reset Blur My Shell and Dash to Dock settings
    dconf write /org/gnome/shell/extensions/dash-to-dock/extend-height false
    dconf write /org/gnome/shell/extensions/blur-my-shell/dash-to-dock/pipeline "'pipeline_default'"
    dconf reset /org/gnome/shell/extensions/blur-my-shell/pipelines

    echo "Reverted to defaults. Please log out for a full refresh."

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
    if ! rpm-ostree kargs | grep -q "vfio-pci.ids=$NV_IDS"; then
        echo "Binding dead dGPU to vfio-pci to force D3 sleep state..."
        
        # 1. rd.driver.pre=vfio-pci : Loads the stub driver into the initramfs before anything else.
        # 2. vfio-pci.ids=... : Tells the stub driver to permanently claim your specific Acer GPU.
        # 3. module_blacklist : Failsafe to ensure nouveau/nvidia don't race the stub driver and hit the bad VRAM.
        sudo rpm-ostree kargs \
            --append-if-missing="rd.driver.pre=vfio-pci" \
            --append-if-missing="vfio-pci.ids=$NV_IDS" \
            --append-if-missing="module_blacklist=nouveau" \
            --append-if-missing="module_blacklist=nvidia"
            
        echo "Success! The dead dGPU will be permanently isolated and put to sleep on the next reboot."
    else
        echo "The Acer dGPU is already quarantined. No action needed."
    fi

apply-hardware-quirks:
    #!/usr/bin/bash
    set -euo pipefail
    SERIAL=$(sudo cat /sys/class/dmi/id/product_serial 2>/dev/null || true)
    QUIRK=$(/usr/bin/redfox-config get-quirk "$SERIAL" 2>/dev/null || true)
    if [ -n "$QUIRK" ]; then
        echo "Hardware match found! Applying quirk: $QUIRK"
        just "$QUIRK"
    else
        echo "No specific hardware quirks mapped for this device."
    fi

# Configure NordVPN silently (relies on redfox-nord config or secrets)
configure-nordvpn:
    @echo "Configuring NordVPN WireGuard connections..."
    /usr/bin/redfox-nord sync || echo "[WARN] redfox-nord sync could not complete (offline or missing token)."

# Nuke all VPN connections
nuke-vpns:
    @echo "WARNING: This will permanently delete all configured VPNs."
    /usr/bin/redfox-nord nuke -y

# Synchronize NordVPN WireGuard fleet against active profile
nord-sync:
    /usr/bin/redfox-nord sync

# List installed NordVPN connections
nord-list:
    /usr/bin/redfox-nord list

# Add a NordVPN connection (e.g. just nord-add US --p2p)
nord-add *args:
    /usr/bin/redfox-nord add {{args}}

# Remove a NordVPN connection (e.g. just nord-remove US)
nord-remove target:
    /usr/bin/redfox-nord remove {{target}}

# Enable weekly ClamAV antivirus scans
enable-clamav-weekly:
    sudo systemctl enable --now clamscan-weekly.timer
    systemctl list-timers clamscan-weekly.timer

# Disable weekly ClamAV antivirus scans
disable-clamav-weekly:
    sudo systemctl disable --now clamscan-weekly.timer

# Create and enable a swapfile (Default: 16G)
add-swap size="16G":
    #!/usr/bin/bash
    set -euo pipefail
    
    # Calculate exact bytes requested (e.g., 16G = 17179869184)
    REQ_BYTES=$(numfmt --from=iec {{size}})
    
    if [ -f /var/swapfile ] && swapon --show | grep -q "/var/swapfile"; then
        CUR_BYTES=$(stat -c "%s" /var/swapfile 2>/dev/null || echo "0")
        if [ "$CUR_BYTES" == "$REQ_BYTES" ]; then
            echo "[OK] Swapfile already active at requested size ({{size}})."
            exit 0
        fi
        echo "Swap size mismatch. Resizing to {{size}}..."
        sudo swapoff /var/swapfile
        sudo rm -f /var/swapfile
    fi

    echo "Creating {{size}} swapfile in /var/swapfile..."
    # We use the native btrfs command to safely handle Copy-On-Write (NOCOW) requirements
    sudo btrfs filesystem mkswapfile --size {{size}} /var/swapfile
    sudo swapon /var/swapfile
    
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

# Install Basic Apps
install-basic:
    flatpak install -y flathub \
        org.gnome.World.PikaBackup \
        org.gnome.Calendar \
        org.gnome.Snapshot \
        org.gnome.clocks \
        org.gnome.Contacts \
        org.gnome.Maps \
        org.gnome.Weather

# Install Productivity Apps
install-productivity:
    flatpak install -y flathub \
        org.gnome.SimpleScan \
        org.libreoffice.LibreOffice \
        com.getmailspring.Mailspring \
        be.alexandervanhee.gradia \
        net.cozic.joplin_desktop \
        app.drey.Warp
# Consider OnlyOffice for PDF capabilities

# Install Communication Apps
install-comms:
    flatpak install -y flathub \
        org.signal.Signal \
        dev.vencord.Vesktop

# Install Daily Apps
install-daily:
    flatpak install -y flathub \
        dev.geopjr.Tuba \
        io.gitlab.news_flash.NewsFlash \
        com.github.geigi.cozy \
        com.github.johnfactotum.Foliate \
        org.gnome.Music \
        com.spotify.Client

# Install Audio Production Apps
install-audio: install-soundthread
    flatpak install -y flathub \
        org.ardour.Ardour \
        info.puredata.Pd \
        net.purrdata.PurrData \
        org.audacityteam.Audacity \
        net.sourceforge.VMPK \
        org.pipewire.Helvum
# Consider FamiStudio

# Install Graphics Apps
install-graphics:
    flatpak install -y flathub \
        org.kde.krita \
        org.blender.Blender \
        org.inkscape.Inkscape \
        org.gimp.GIMP \
        com.orama_interactive.Pixelorama \
        nl.hjdskes.gcolor3 \
        net.pixieditor.PixiEditor

# Install Photography Apps
install-photos:
    flatpak install -y flathub \
        org.kde.digikam \
        org.darktable.Darktable

# Install Video Production Apps
install-video:
    flatpak install -y flathub \
        org.kde.kdenlive \
        org.bunkus.mkvtoolnix-gui \
        org.gnome.gitlab.YaLTeR.VideoTrimmer \
        com.github.unrud.VideoDownloader \
        com.obsproject.Studio \
        io.github.wartybix.Constrict

# Install Compatibility Tools
install-compatibility: install-winboat
    flatpak install -y flathub \
        com.usebottles.bottles

# Install Music Notation Apps
install-notation:
    flatpak install -y flathub \
        org.musescore.MuseScore \
        org.frescobaldi.Frescobaldi

# Install Writing Apps
install-writing:
    flatpak install -y flathub \
        org.cvfosammmm.Setzer \
        ch.theologeek.Manuskript

# Install GNOME Development Apps
install-gnome-dev:
    flatpak install -y flathub \
        org.gnome.Builder \
        re.sonny.Workbench

# Install Development Apps
install-dev: install-gnome-dev install-zed install-antigravity-cli
    flatpak install -y flathub \
        io.podman_desktop.PodmanDesktop \
        org.gnome.dspy \
        ca.desrt.dconf-editor

# Install Bluefin DX Extras
install-bluefin-dx:
    flatpak install -y flathub \
        org.freedesktop.Bustle \
        de.leopoldluley.Clapgrep \
        io.github.ronniedroid.concessio \
        me.iepure.devtoolbox \
        io.github.getnf.embellish \
        org.pipewire.Helvum

# Install Creative Suite
install-creative: install-audio install-graphics install-photos install-video install-notation install-writing


# Level 2: Molecules (Logical Groups)

# Install Matt's Bundle
install-matt: install-dev install-bluefin-dx install-creative install-daily install-productivity install-compatibility install-basic install-comms
    flatpak install -y flathub \
        com.jeffser.Alpaca

# Install Dewy's Bundle
install-dewy: install-zed install-comms
    flatpak install -y flathub \
        org.videolan.VLC \
        net.pixieditor.PixiEditor \
        com.spotify.Client \
        com.bambulab.BambuStudio \
        org.gnome.SimpleScan \
        org.libreoffice.LibreOffice \
        be.alexandervanhee.gradia \
        net.cozic.joplin_desktop \
        app.drey.Warp \
        org.texstudio.TeXstudio \
        com.brave.Browser \
        com.slack.Slack \
        com.dropbox.Client
    echo "Installing latest TexLive extension..."
    flatpak install -y flathub "org.freedesktop.Sdk.Extension.texlive//$(flatpak remote-ls flathub --columns=application,branch | grep org.freedesktop.Sdk.Extension.texlive | awk '{print $2}' | sort -V | tail -n 1)"
# Install Normie Bundle
install-normie: install-basic install-daily install-productivity install-comms


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
    dconf write /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/']"
    
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
    # Note: We leave the custom-keybindings array alone or empty it if this was the only one
    dconf write /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings "@as []"
    
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

# Configure Dev Environment
configure-dev: configure-vscode configure-cursor configure-antigravity

# Configure Matt's Environment
configure-matt: redfox-enforce-config apply-hardware-quirks add-swap configure-nordvpn reset-hostname configure-keybindings-default configure-dev configure-text-editor-dev configure-terminal-default configure-powersaver-no-suspend configure-xway-scale-off
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

# Configure Dewy's Environment
configure-dewy: redfox-enforce-config configure-keybindings-default configure-text-editor-dev reset-hostname configure-cursor-dewy configure-terminal-tilix configure-nordvpn configure-powersaver-default configure-xway-scale-on enable-clamav-weekly
    gsettings set org.gnome.shell.keybindings show-screenshot-ui "['Print']"
    gsettings set org.gnome.shell.keybindings screenshot "['<Shift><Super>s']"
    gnome-extensions disable unblank@sun.wxg@gmail.com

# Configure Fedora's Environment
configure-fedora: configure-keybindings-default configure-text-editor-reset reset-hostname configure-powersaver-default configure-xway-scale-on
    gnome-extensions disable unblank@sun.wxg@gmail.com

# Configure Normie's Environment
configure-normie: configure-keybindings-default configure-text-editor-reset reset-hostname configure-powersaver-no-suspend configure-xway-scale-off
    gnome-extensions enable unblank@sun.wxg@gmail.com


# --- LAYOUT MOLECULES (UX/Behavior/Positioning) ---

# Layout Matt
layout-matt: sort-app-grid set-window-controls-left-gnome layout-tiling-default preset-dock-gnome
    gsettings reset-recursively org.gnome.shell.extensions.dash-to-dock
    gsettings set org.gnome.shell favorite-apps "[\
      'org.gnome.Ptyxis.desktop', \
      'org.gnome.Nautilus.desktop', \
      'com.getmailspring.Mailspring.desktop', \
      'org.mozilla.firefox.desktop', \
      'org.signal.Signal.desktop', \
      'org.gnome.TextEditor.desktop', \
      'antigravity-ide.desktop', \
      'com.spotify.Client.desktop', \
      'steam.desktop', \
      'net.cozic.joplin_desktop.desktop', \
      'io.github.kolunmi.Bazaar.desktop', \
      'org.gnome.Settings.desktop']"
    # Note: Add Gemini Web App ID and Dorico 6 once stabilized.

# Layout Dewy
layout-dewy: sort-app-grid set-window-controls-right-full layout-tiling-dewy preset-dock-ubuntu
    gsettings set org.gnome.shell.extensions.dash-to-dock isolate-workspaces true
    gsettings set org.gnome.shell.extensions.dash-to-dock dash-max-icon-size 40
    gsettings set org.gnome.shell favorite-apps "['org.gnome.Nautilus.desktop', 'io.missioncenter.MissionCenter.desktop', 'org.gnome.Settings.desktop', 'org.gnome.Ptyxis.desktop', 'org.mozilla.firefox.desktop', 'com.brave.Browser.desktop', 'org.gnome.Calculator.desktop', 'org.gnome.TextEditor.desktop', 'dev.zed.Zed.desktop', 'cursor.desktop', 'com.spotify.Client.desktop', 'com.slack.Slack.desktop', 'org.signal.Signal.desktop', 'dev.vencord.Vesktop.desktop']"

# Layout Fedora (Mostly Vanilla Fedora 43 Defaults)
layout-fedora: default-app-grid set-window-controls-right-gnome layout-tiling-default preset-dock-gnome
    gsettings reset-recursively org.gnome.shell.extensions.dash-to-dock
    gsettings set org.gnome.shell favorite-apps "['org.mozilla.firefox.desktop', 'org.gnome.Calendar.desktop', 'org.gnome.Nautilus.desktop', 'io.github.kolunmi.Bazaar.desktop', 'org.gnome.TextEditor.desktop', 'org.gnome.Calculator.desktop']"

# Layout Normie (Consumer-focused Experience)
layout-normie: default-app-grid set-window-controls-left-gnome layout-tiling-default
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
      'org.gnome.Settings.desktop']"

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
bootstrap-matt: configure-matt install-matt theme-matt layout-matt _print-bootstrap-recap
# Bootstrap Dewy
bootstrap-dewy: configure-dewy install-dewy theme-dewy layout-dewy _print-bootstrap-recap

# Bootstrap Fedora
bootstrap-fedora: theme-fedora layout-fedora configure-fedora _print-bootstrap-recap

# Bootstrap Normie
bootstrap-normie: install-normie theme-normie layout-normie configure-normie _print-bootstrap-recap

# Level 1: Atoms (Single-Purpose Scripts)

# Setup Secrets (The "Front Desk" Pattern)
# This recipe MUST be the first dependency for any recipe chain requiring secrets or sudo.
# It runs exactly once per `just` invocation, caching sudo and downloading required secrets.
redfox-init-secrets:
    #!/usr/bin/bash
    set -euo pipefail

    echo "================================================================="
    echo "                 RedFoxOS Secrets Setup                          "
    echo "================================================================="
    
    # 1. Cache Sudo Immediately
    echo "Please provide your password to cache sudo for this setup run."
    sudo -v

    # Keep sudo alive in the background until this script exits
    while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

    # 2. Check if secrets already exist
    SECRETS_DIR="$HOME/.config/redfox"
    SECRETS_FILE="$SECRETS_DIR/secrets.env"
    
    if [ -f "$SECRETS_FILE" ]; then
        echo "[OK] Secrets already configured."
        exit 0
    fi

    mkdir -p "$SECRETS_DIR"
    
    # 3. Prompt for Gist URL
    echo -e "\nPlease provide the base RAW URL of your secret RedFox Gist."
    echo "Example: https://gist.githubusercontent.com/username/hash/raw"
    read -p "Gist URL: " GIST_URL
    
    # Remove trailing slash if present
    GIST_URL=${GIST_URL%/}

    # Download Gist files
    echo -e "\nDownloading configurations..."
    curl -sS -f -o "$SECRETS_DIR/hardware-mapping.txt" "$GIST_URL/hardware-mapping.txt" || echo "  [WARN] Could not download hardware-mapping.txt"
    curl -sS -f -o "$SECRETS_DIR/nordvpn-connections.txt" "$GIST_URL/nordvpn-connections.txt" || echo "  [WARN] Could not download nordvpn-connections.txt"

    # 4. Prompt for VPN Credentials
    echo -e "\n-----------------------------------------------------------------"
    echo "                  NordVPN Credentials Required                   "
    echo "-----------------------------------------------------------------"
    echo " NOTE: Do NOT use your standard NordVPN email and password."
    echo " You must use your NordVPN 'Service Credentials' (a long string"
    echo " of random characters). Find these on your Nord Account"
    echo " dashboard under: Services > NordVPN > Manual setup."
    echo "-----------------------------------------------------------------"
    read -p "Service Username: " VPN_USER
    read -sp "Service Password: " VPN_PASS
    echo ""

    # 5. Save securely
    echo "VPN_USER=\"$VPN_USER\"" > "$SECRETS_FILE"
    echo "VPN_PASS=\"$VPN_PASS\"" >> "$SECRETS_FILE"
    chmod 600 "$SECRETS_FILE"

    echo -e "\n[SUCCESS] Secrets setup complete."

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

# Configure Text Editor Dev Mode (Indentation)
configure-text-editor-dev:
    echo "Configuring Text Editor for Development (Spaces, 4 per tab)..."
    flatpak run --command=gsettings org.gnome.TextEditor set org.gnome.TextEditor indent-style 'space'
    flatpak run --command=gsettings org.gnome.TextEditor set org.gnome.TextEditor tab-width 4

# Reset Text Editor Configuration (Indentation)
configure-text-editor-reset:
    echo "Resetting Text Editor indentation to defaults..."
    flatpak run --command=gsettings org.gnome.TextEditor reset org.gnome.TextEditor indent-style
    flatpak run --command=gsettings org.gnome.TextEditor reset org.gnome.TextEditor tab-width

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

# Install Gemini CLI
install-gemini-cli:
    echo "Installing Gemini CLI..."
    brew install gemini-cli
    echo "Gemini CLI installed!"

# Uninstall Gemini CLI
uninstall-gemini-cli:
    echo "Uninstalling Gemini CLI..."
    brew uninstall gemini-cli
    echo "Gemini CLI uninstalled!"

# Configure Heroic
configure-heroic:
    echo "TODO: Implement configure-heroic"

# Install SoundThread
install-soundthread:
    /usr/bin/update-soundthread

# Uninstall SoundThread
uninstall-soundthread:
    /usr/bin/uninstall-soundthread

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

preset-dock-ubuntu:
    gsettings reset-recursively org.gnome.shell.extensions.dash-to-dock
    gnome-extensions enable dash-to-dock@micxgx.gmail.com

preset-dock-gnome:
    gnome-extensions disable dash-to-dock@micxgx.gmail.com

preset-dock-win-classic:
    echo "TODO: Implement preset-dock-win-classic"

preset-dock-win-new:
    echo "TODO: Implement preset-dock-win-new"

preset-dock-macos:
    echo "TODO: Implement preset-dock-macos"

# Hardware Atoms
fix-oryp9-mouse:
    @echo "Applying udev rule to ignore ghost PS/2 mouse..."
    @echo 'ACTION=="add|change", KERNEL=="event*", ATTRS{name}=="*PS/2*Mouse", ENV{LIBINPUT_IGNORE_DEVICE}="1"' | sudo tee /etc/udev/rules.d/99-block-ghost-mouse.rules
    @echo "Reloading udev rules..."
    @sudo udevadm control --reload-rules && sudo udevadm trigger
    @echo "Done."

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

apply-hardware-quirks: redfox-init-secrets
    #!/usr/bin/bash
    set -euo pipefail
    
    MAPPING_FILE="$HOME/.config/redfox/hardware-mapping.txt"
    if [ ! -f "$MAPPING_FILE" ]; then
        echo "No hardware mapping file found at $MAPPING_FILE. Skipping hardware quirks."
        exit 0
    fi
    
    # Require sudo to read the DMI serial safely
    # (Since redfox-init-secrets just ran, this won't prompt)
    SERIAL=$(sudo cat /sys/class/dmi/id/product_serial 2>/dev/null || echo "Unknown")
    
    if [ "$SERIAL" == "Unknown" ]; then
        echo "Could not read hardware serial number. Skipping hardware quirks."
        exit 0
    fi
    
    echo "Checking for hardware quirks for this device..."
    
    # Look for a line matching 'SERIAL:QUIRK_NAME'
    QUIRK=$(grep "^${SERIAL}:" "$MAPPING_FILE" | cut -d':' -f2 || true)
    
    if [ -n "$QUIRK" ]; then
        echo "Hardware match found! Applying quirk: $QUIRK"
        just "$QUIRK"
    else
        echo "No specific hardware quirks mapped for this device."
    fi

# Configure NordVPN silently (relies on redfox-init-secrets)
configure-nordvpn: redfox-init-secrets
    @echo "Configuring NordVPN..."
    sudo /usr/bin/import-nord-configs

# Nuke all VPN connections
nuke-vpns:
    @echo "WARNING: This will permanently delete all configured VPNs."
    sudo /usr/bin/nuke-vpn-configs

# Create and enable a swapfile (Default: 16G)
add-swap size="16G":
    #!/usr/bin/bash
    set -euo pipefail
    echo "Creating {{size}} swapfile in /var/swapfile..."
    # We use the native btrfs command to safely handle Copy-On-Write (NOCOW) requirements
    sudo btrfs filesystem mkswapfile --size {{size}} /var/swapfile
    sudo swapon /var/swapfile
    echo "Making swap persistent in /etc/fstab..."
    # Check if it already exists to avoid duplicate entries
    if ! grep -q '^/var/swapfile' /etc/fstab; then
        echo "/var/swapfile none swap defaults 0 0" | sudo tee -a /etc/fstab
    fi
    echo "Swapfile successfully created and enabled!"
    swapon --show | grep "/var/swapfile"

# Disable and remove the swapfile
remove-swap:
    #!/usr/bin/bash
    set -euo pipefail
    echo "Disabling swapfile..."
    sudo swapoff /var/swapfile || true
    echo "Removing from /etc/fstab..."
    # Safely delete the line starting with /var/swapfile from fstab
    sudo sed -i '/^\/var\/swapfile/d' /etc/fstab
    echo "Deleting the swapfile..."
    sudo rm -f /var/swapfile
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
install-dev: install-gnome-dev install-zed install-gemini-cli
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
    nautilus -q
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
    dconf write /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings "[]"
    
    # 3. Reload Nautilus
    nautilus -q
    @echo "Done. Restored to Ptyxis."

# Configure Power Saver, Suspend (default)
configure-powersaver-default:
    gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'suspend'

# Configure Power Saver, No Suspend (tweak)
configure-powersaver-no-suspend:
    gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'

# Disable xwayland-native-scaling (Deviation)
configure-xway-scale-off:
    #!/usr/bin/bash
    CURRENT=$(gsettings get org.gnome.mutter experimental-features)
    NEW=$(python3 -c "import sys, ast; val=sys.argv[1]; val=val[4:] if val.startswith('@as ') else val; val='[]' if not val else val; lst=ast.literal_eval(val) if val != '[]' else []; lst.remove('xwayland-native-scaling') if 'xwayland-native-scaling' in lst else None; print(repr(lst))" "$CURRENT" 2>/dev/null || echo "[]")
    gsettings set org.gnome.mutter experimental-features "$NEW"
    echo "Disabled xwayland-native-scaling"

# Enable xwayland-native-scaling (Deviation)
configure-xway-scale-on:
    #!/usr/bin/bash
    CURRENT=$(gsettings get org.gnome.mutter experimental-features)
    NEW=$(python3 -c "import sys, ast; val=sys.argv[1]; val=val[4:] if val.startswith('@as ') else val; val='[]' if not val else val; lst=ast.literal_eval(val) if val != '[]' else []; lst.append('xwayland-native-scaling') if 'xwayland-native-scaling' not in lst else None; print(repr(lst))" "$CURRENT" 2>/dev/null || echo "['xwayland-native-scaling']")
    gsettings set org.gnome.mutter experimental-features "$NEW"
    echo "Enabled xwayland-native-scaling"

# Configure Dev Environment
configure-dev: configure-vscode configure-cursor

# Configure Matt's Environment
configure-matt: setup-secrets apply-hardware-quirks add-swap configure-nordvpn reset-hostname configure-keybindings-default configure-dev configure-text-editor-dev configure-terminal-default configure-powersaver-no-suspend configure-xway-scale-off
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
    if [ -f "$SETTINGS_FILE" ]; then
        tmp=$(mktemp)
        jq '."workbench.colorTheme" = "Default Dark Modern"' "$SETTINGS_FILE" > "$tmp" && mv "$tmp" "$SETTINGS_FILE"
    else
        echo '{"workbench.colorTheme": "Default Dark Modern"}' > "$SETTINGS_FILE"
    fi

# Configure Dewy's Environment
configure-dewy: setup-secrets configure-keybindings-default configure-text-editor-dev reset-hostname configure-cursor-dewy configure-terminal-tilix configure-nordvpn configure-powersaver-default configure-xway-scale-on
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

# Layout Dewy
layout-dewy: sort-app-grid set-window-controls-right-full layout-tiling-dewy preset-dock-ubuntu
    gsettings set org.gnome.shell.extensions.dash-to-dock isolate-workspaces true
    gsettings set org.gnome.shell.extensions.dash-to-dock dash-max-icon-size 40
    gsettings set org.gnome.shell favorite-apps "['org.gnome.Nautilus.desktop', 'io.missioncenter.MissionCenter.desktop', 'org.gnome.Settings.desktop', 'org.gnome.Ptyxis.desktop', 'org.mozilla.firefox.desktop', 'com.brave.Browser.desktop', 'org.gnome.Calculator.desktop', 'org.gnome.TextEditor.desktop', 'dev.zed.Zed.desktop', 'cursor.desktop', 'com.spotify.Client.desktop', 'com.slack.Slack.desktop', 'org.signal.Signal.desktop', 'dev.vencord.Vesktop.desktop']"

# Layout Fedora (Vanilla)
layout-fedora: default-app-grid set-window-controls-right-gnome layout-tiling-default preset-dock-gnome
    gsettings reset-recursively org.gnome.shell.extensions.dash-to-dock

# Layout Normie (Flexible)
layout-normie: default-app-grid set-window-controls-left-gnome layout-tiling-default
    echo "TODO: Implement layout-normie"


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
bootstrap-matt: configure-matt install-matt theme-matt layout-matt

# Bootstrap Dewy
bootstrap-dewy: configure-dewy install-dewy theme-dewy layout-dewy

# Bootstrap Fedora
bootstrap-fedora: theme-fedora layout-fedora configure-fedora

# Bootstrap Normie
bootstrap-normie: install-normie theme-normie layout-normie configure-normie

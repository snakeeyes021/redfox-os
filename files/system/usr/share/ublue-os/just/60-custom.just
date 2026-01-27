# Level 1: Atoms (Single-Purpose Scripts)

# Configure Git
configure-git:
    echo "TODO: Implement configure-git"

# Configure VSCode
configure-vscode:
    echo "TODO: Implement configure-vscode"

# Configure Cursor
configure-cursor:
    echo "TODO: Implement configure-cursor"

# Install Zed
install-zed:
    echo "TODO: Implement install-zed"

# Install Gemini CLI
install-gemini-cli:
    echo "TODO: Implement install-gemini-cli"

# Install Dropbox
install-dropbox:
    echo "TODO: Implement install-dropbox (maestral)"

# Configure Heroic
configure-heroic:
    echo "TODO: Implement configure-heroic"

# Install SoundThread
install-soundthread:
    echo "TODO: Implement install-soundthread"

# Install Winboat (via Gearlever)
# Install Winboat (via Gearlever)
install-winboat:
    #!/usr/bin/env bash
    set -e # Exit immediately if a command fails
    echo "Installing Winboat..."
    flatpak install -y flathub it.mijorus.gearlever
    
    echo "Fetching latest Winboat AppImage..."
    # No $$ needed here because we are inside a bash shebang block!
    # No && \ needed because variables persist in this block.
    URL=$(curl -s https://api.github.com/repos/TibixDev/winboat/releases/latest | jq -r '.assets[] | select(.name | test("x86_64.AppImage$")) | .browser_download_url')
    
    if [ -z "$URL" ]; then
        echo "Error: Could not find download URL"
        exit 1
    fi

    curl -L -o /tmp/WinBoat.AppImage "$URL"
    echo "Opening in Gearlever..."
    flatpak run it.mijorus.gearlever /tmp/WinBoat.AppImage

# Update Gearlever AppImages
update-gearlever:
    #!/usr/bin/bash
    if ! flatpak list | grep -q "it.mijorus.gearlever"; then
        echo "Gearlever not installed. Skipping."
        exit 0
    fi
    APPS=$(flatpak run it.mijorus.gearlever --list-installed)
    if [ -z "$APPS" ]; then
        echo "No AppImages managed by Gearlever found."
        exit 0
    fi
    echo "=== Updating Gearlever AppImages ==="
    echo "$APPS" | while read -r APP_PATH; do
        if [ -n "$APP_PATH" ]; then
            APP_NAME=$(basename "$APP_PATH")
            echo "-> Checking $APP_NAME..."
            flatpak run it.mijorus.gearlever --update "$APP_PATH"
        fi
    done

# UI/UX Atoms
fix-flatpak-theming:
    sudo flatpak override --filesystem=xdg-data/themes
    sudo flatpak mask org.gtk.Gtk3theme.adw-gtk3
    sudo flatpak mask org.gtk.Gtk3theme.adw-gtk3-dark

set-window-controls-right:
    echo "TODO: Implement set-window-controls-right"

set-window-controls-left-gnome:
    echo "TODO: Implement set-window-controls-left-gnome"

sort-app-grid:
    echo "TODO: Implement sort-app-grid"

default-app-grid:
    echo "TODO: Implement default-app-grid"

preset-dock-ubuntu:
    echo "TODO: Implement preset-dock-ubuntu"

preset-dock-win-classic:
    echo "TODO: Implement preset-dock-win-classic"

preset-dock-win-new:
    echo "TODO: Implement preset-dock-win-new"

preset-dock-macos:
    echo "TODO: Implement preset-dock-macos"

# Hardware Atoms
fix-oryp9-mouse:
    echo "TODO: Implement fix-oryp9-mouse"

fix-acer-nouveau:
    echo "TODO: Implement fix-acer-nouveau"

fix-4k-scaling:
    echo "TODO: Implement fix-4k-scaling"


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
        org.gnome.Music

# Install Audio Production Apps
install-audio:
    just install-soundthread
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
        nl.hjdskes.gcolor3

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
        com.obsproject.Studio

# Install Compatibility Tools
install-compatibility:
    just install-winboat
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
install-dev:
    just install-gnome-dev
    just install-zed
    just install-gemini-cli
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
install-creative:
    just install-audio
    just install-graphics
    just install-photos
    just install-video
    just install-notation
    just install-writing


# Level 2: Molecules (Logical Groups)

# Install Matt's Bundle
install-matt:
    just install-dev
    just install-bluefin-dx
    just install-creative
    just install-daily
    just install-productivity
    just install-compatibility
    just install-basic
    just install-comms

# Install Dewy's Bundle
install-dewy:
    just install-zed
    just install-dropbox
    just install-basic
    just install-daily
    just install-productivity
    just install-comms
    flatpak install -y flathub \
        org.videolan.VLC \
        org.cvfosammmm.Setzer

# Install Normie Bundle
install-normie:
    just install-basic
    just install-daily
    just install-productivity
    just install-comms


# Level 3: Organisms (User Bootstraps & Configs)

# Configure Dev Environment
configure-dev:
    just configure-vscode
    just configure-cursor

# Configure Matt's Environment
configure-matt:
    mkdir -p ~/dev
    just configure-dev
    # just runs hardware atoms here eventually

# Configure Dewy's Environment
configure-dewy:
    echo "TODO: Implement configure-dewy"

# Configure Fedora's Environment
configure-fedora:
    echo "TODO: Implement configure-fedora"

# Configure Normie's Environment
configure-normie:
    echo "TODO: Implement configure-normie"

# Theme Matt
theme-matt:
    just sort-app-grid
    just set-window-controls-left-gnome

# Theme Dewy
theme-dewy:
    just sort-app-grid
    just set-window-controls-right
    just preset-dock-ubuntu

# Theme Fedora
theme-fedora:
    echo "TODO: Implement theme-fedora (reset)"

# Theme Normie
theme-normie:
    echo "TODO: Implement theme-normie"

# Bootstrap Matt
bootstrap-matt:
    just install-matt
    just theme-matt
    just configure-matt

# Bootstrap Dewy
bootstrap-dewy:
    just install-dewy
    just theme-dewy
    just configure-dewy

# Bootstrap Fedora
bootstrap-fedora:
    just theme-fedora
    just configure-fedora

# Bootstrap Normie
bootstrap-normie:
    just install-normie
    just theme-normie
    just configure-normie

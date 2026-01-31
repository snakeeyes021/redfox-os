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

# Install Dropbox
install-dropbox:
    echo "Installing Maestral (Dropbox Client)..."
    pip install --upgrade 'maestral[gui]'
    echo "Maestral installed!"

# Uninstall Dropbox
uninstall-dropbox:
    echo "Uninstalling Maestral (Dropbox Client)..."
    pip uninstall -y maestral
    echo "Maestral uninstalled!"

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
        org.gnome.Music \
        com.spotify.Client

# Install Audio Production Apps
install-audio:
    install-soundthread
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
        com.obsproject.Studio

# Install Compatibility Tools
install-compatibility:
    install-winboat
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
    install-gnome-dev
    install-zed
    install-gemini-cli
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
    install-audio
    install-graphics
    install-photos
    install-video
    install-notation
    install-writing


# Level 2: Molecules (Logical Groups)

# Install Matt's Bundle
install-matt:
    install-dev
    install-bluefin-dx
    install-creative
    install-daily
    install-productivity
    install-compatibility
    install-basic
    install-comms

# Install Dewy's Bundle
install-dewy:
    install-zed
    install-dropbox
    install-basic
    install-productivity
    install-comms
    flatpak install -y flathub \
        org.videolan.VLC \
        org.cvfosammmm.Setzer \
        net.pixieditor.PixiEditor \
        com.spotify.Client

# Install Normie Bundle
install-normie:
    install-basic
    install-daily
    install-productivity
    install-comms


# Level 3: Organisms (User Bootstraps & Configs)

# Configure Dev Environment
configure-dev:
    configure-vscode
    configure-cursor

# Configure Matt's Environment
configure-matt:
    mkdir -p ~/dev
    configure-dev
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
    sort-app-grid
    set-window-controls-left-gnome

# Theme Dewy
theme-dewy:
    sort-app-grid
    set-window-controls-right
    preset-dock-ubuntu

# Theme Fedora
theme-fedora:
    echo "TODO: Implement theme-fedora (reset)"

# Theme Normie
theme-normie:
    echo "TODO: Implement theme-normie"

# Bootstrap Matt
bootstrap-matt:
    install-matt
    theme-matt
    configure-matt

# Bootstrap Dewy
bootstrap-dewy:
    install-dewy
    theme-dewy
    configure-dewy

# Bootstrap Fedora
bootstrap-fedora:
    theme-fedora
    configure-fedora

# Bootstrap Normie
bootstrap-normie:
    install-normie
    theme-normie
    configure-normie

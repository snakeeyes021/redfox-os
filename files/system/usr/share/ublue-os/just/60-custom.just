# Level 1: Atoms (Single-Purpose Scripts)

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
install-dewy: install-zed install-dropbox install-comms
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
        org.freedesktop.Sdk.Extension.texlive

# Install Normie Bundle
install-normie: install-basic install-daily install-productivity install-comms


# Level 3: Organisms (User Bootstraps & Configs)

# --- CONFIG MOLECULES (User/Tool Setup) ---

# Configure Dev Environment
configure-dev: configure-vscode configure-cursor

# Configure Matt's Environment
configure-matt: configure-dev configure-text-editor-dev reset-hostname
    mkdir -p ~/dev
    # just runs hardware atoms here eventually
    # e.g., fix-oryp9-mouse

# Configure Dewy's Environment
configure-dewy: configure-text-editor-dev reset-hostname

# Configure Fedora's Environment
configure-fedora: configure-text-editor-reset reset-hostname
    echo "TODO: Implement configure-fedora"

# Configure Normie's Environment
configure-normie: configure-text-editor-reset reset-hostname
    echo "TODO: Implement configure-normie"


# --- LAYOUT MOLECULES (UX/Behavior/Positioning) ---

# Layout Matt (Mac-like)
layout-matt: sort-app-grid set-window-controls-left-gnome layout-tiling-default
    # preset-dock-macos

# Layout Dewy (Windows/Ubuntu-like)
layout-dewy: sort-app-grid set-window-controls-right-full layout-tiling-dewy preset-dock-ubuntu

# Layout Fedora (Vanilla)
layout-fedora: default-app-grid set-window-controls-right-gnome layout-tiling-default
    echo "TODO: Implement layout-fedora (reset)"

# Layout Normie (Flexible)
layout-normie: default-app-grid set-window-controls-left-gnome layout-tiling-default
    echo "TODO: Implement layout-normie"


# --- THEME MOLECULES (Visuals/Assets) ---

# Theme Matt
theme-matt: theme-text-editor-default theme-sound-fedora
    echo "Applying Matt's Visual Theme..."
    # gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita-dark'
    # gsettings set org.gnome.desktop.background picture-uri 'file:///...'

# Theme Dewy
theme-dewy: theme-text-editor-dewy
    echo "Applying Dewy's Visual Theme..."
    # gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita'
    # theme-sound-bazzite

# Theme Fedora
theme-fedora: theme-text-editor-default theme-sound-fedora

# Theme Normie
theme-normie: theme-text-editor-default theme-sound-fedora


# --- BOOTSTRAP ORGANISMS ---

# Bootstrap Matt
bootstrap-matt: install-matt theme-matt layout-matt configure-matt

# Bootstrap Dewy
bootstrap-dewy: install-dewy theme-dewy layout-dewy configure-dewy

# Bootstrap Fedora
bootstrap-fedora: theme-fedora layout-fedora configure-fedora

# Bootstrap Normie
bootstrap-normie: install-normie theme-normie layout-normie configure-normie

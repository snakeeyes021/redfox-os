# vim: set ft=make :

alias upgrade := update

# Run complete system, Flatpak, Brew, and application updates via Topgrade
[group("system")]
update:
    #!/usr/bin/bash
    set -uo pipefail

    TOPGRADE_STATUS=0
    /usr/bin/topgrade --config /usr/share/ublue-os/topgrade.toml || TOPGRADE_STATUS=$?

    # Check if we have an interactive terminal (controlling tty or terminal stdout)
    INTERACTIVE=false
    TTY_IN="/dev/stdin"
    if [ -c /dev/tty ]; then
        INTERACTIVE=true
        TTY_IN="/dev/tty"
    elif [[ -t 0 || -t 1 ]]; then
        INTERACTIVE=true
    fi

    if [ "$INTERACTIVE" = true ]; then
        echo ""
        echo "=================================================="

        if [ "$TOPGRADE_STATUS" -ne 0 ]; then
            echo " ⚠️  Topgrade completed with warning/status code $TOPGRADE_STATUS."
            echo "=================================================="
        fi

        if rpm-ostree status 2>/dev/null | grep -qi "staged"; then
            echo " 🎉 System update complete! A new OS deployment is staged."
            echo "    Updates will take full effect after a reboot."
            echo "=================================================="
            echo ""
            while true; do
                read -r -p "Choose an action: [r]eboot, [d]iff, [c]hangelog, [q]uit (default: q): " CHOICE < "$TTY_IN" || CHOICE="q"
                case "${CHOICE,,}" in
                    r|reboot)
                        echo "Rebooting..."
                        systemctl reboot
                        break
                        ;;
                    d|diff)
                        echo ""
                        rpm-ostree db diff || true
                        echo ""
                        ;;
                    c|changelog|changelogs)
                        echo ""
                        (just changelogs 2>/dev/null || ujust changelogs 2>/dev/null || echo "No changelog available.")
                        echo ""
                        ;;
                    q|quit|"")
                        echo "Exiting. Remember to reboot when convenient."
                        break
                        ;;
                    *)
                        echo "Invalid choice. Please enter 'r', 'd', 'c', or 'q'."
                        ;;
                esac
            done
        else
            echo " 🎉 System & application updates complete!"
            echo "=================================================="
            echo ""
            read -r -p "Press [Enter] to close this window..." _ < "$TTY_IN" || true
        fi
    else
        exit "$TOPGRADE_STATUS"
    fi

alias changelog := changelogs

# Show the stable changelog
[group("system")]
changelogs:
    #!/usr/bin/bash
    CONTENT=$(curl -s https://api.github.com/repos/ublue-os/bazzite/releases/latest | jq -r '.body')
      echo "$CONTENT" | glow -

# Show the testing (pre-release) changelog
[group("system")]
changelogs-testing:
    #!/usr/bin/bash
    CONTENT=$(curl -s https://api.github.com/repos/ublue-os/bazzite/releases/latest | jq -r 'map(select(.prerelease)) | .[0].body')
       echo "$CONTENT" | glow -

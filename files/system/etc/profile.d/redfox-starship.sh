# Use RedFoxOS's Starship settings unless you have your own: the prompt theme
# chosen with `redfox-terminal prompt theme` (or RedFox Hub), RedFox's own
# by default. Worked out again in each new shell, so a new theme shows in new
# terminal windows straight away; a STARSHIP_CONFIG set by anything else is
# left alone.
if [ -z "${STARSHIP_CONFIG:-}" ] || [ "${STARSHIP_CONFIG}" = "${REDFOX_STARSHIP_CONFIG:-}" ]; then
    if [ -e "${XDG_CONFIG_HOME:-$HOME/.config}/starship.toml" ]; then
        [ -n "${REDFOX_STARSHIP_CONFIG:-}" ] && unset STARSHIP_CONFIG
        unset REDFOX_STARSHIP_CONFIG
    else
        _redfox_theme=$(head -n 1 "${XDG_CONFIG_HOME:-$HOME/.config}/redfox/starship-theme" 2>/dev/null)
        _redfox_file=""
        if [ -n "$_redfox_theme" ]; then
            _redfox_file=$(awk -F'\t' -v id="$_redfox_theme" '$1 == id { print $3 }' \
                /usr/share/redfox/starship/themes/themes.tsv 2>/dev/null)
        fi
        export STARSHIP_CONFIG="${_redfox_file:-/usr/share/redfox/starship.toml}"
        export REDFOX_STARSHIP_CONFIG="$STARSHIP_CONFIG"
        unset _redfox_theme _redfox_file
    fi
fi

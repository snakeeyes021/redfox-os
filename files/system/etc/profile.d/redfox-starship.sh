# Use RedFoxOS's Starship settings unless you have your own.
if [ -z "${STARSHIP_CONFIG:-}" ] && [ ! -e "${XDG_CONFIG_HOME:-$HOME/.config}/starship.toml" ]; then
    export STARSHIP_CONFIG=/usr/share/redfox/starship.toml
fi

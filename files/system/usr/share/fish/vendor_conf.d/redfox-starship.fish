# Use RedFoxOS's Starship settings unless you have your own: the prompt theme
# chosen with `redfox-terminal prompt theme` (or RedFox Hub), RedFox's own by
# default. See /etc/profile.d/redfox-starship.sh.
if not set -q STARSHIP_CONFIG; or test "$STARSHIP_CONFIG" = "$REDFOX_STARSHIP_CONFIG"
    set -l config_home (set -q XDG_CONFIG_HOME; and echo $XDG_CONFIG_HOME; or echo $HOME/.config)
    if test -e $config_home/starship.toml
        set -q REDFOX_STARSHIP_CONFIG; and set -e STARSHIP_CONFIG
        set -e REDFOX_STARSHIP_CONFIG
    else
        set -l theme (head -n 1 $config_home/redfox/starship-theme 2>/dev/null)
        set -l file
        if test -n "$theme"
            set file (awk -F'\t' -v id="$theme" '$1 == id { print $3 }' /usr/share/redfox/starship/themes/themes.tsv 2>/dev/null)
        end
        test -n "$file"; or set file /usr/share/redfox/starship.toml
        set -gx STARSHIP_CONFIG $file
        set -gx REDFOX_STARSHIP_CONFIG $file
    end
end

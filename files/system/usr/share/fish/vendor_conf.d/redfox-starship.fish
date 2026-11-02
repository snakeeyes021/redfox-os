# Use RedFoxOS's Starship settings unless you have your own.
if not set -q STARSHIP_CONFIG
    set -l config_home (set -q XDG_CONFIG_HOME; and echo $XDG_CONFIG_HOME; or echo $HOME/.config)
    if not test -e $config_home/starship.toml
        set -gx STARSHIP_CONFIG /usr/share/redfox/starship.toml
    end
end

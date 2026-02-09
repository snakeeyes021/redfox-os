# pixi-path.fish
# Always add pixi bin to PATH so it works immediately after first install
# We use -P (prepend) and -g (global/session only) because this file is sourced on every login.
fish_add_path -P -g "$HOME/.pixi/bin"

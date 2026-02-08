# pixi-path.sh
# Add pixi global bin to PATH if it exists
if [ -d "$HOME/.pixi/bin" ] ; then
    PATH="$HOME/.pixi/bin:$PATH"
fi

#!/usr/bin/env bash
# Tests RedFox Dim in a throwaway headless GNOME Shell: its own D-Bus session,
# home-like directories and settings, nothing shared with the running desktop.
#
#   tests/redfox-dim/run.sh
#
# Run it when moving to a new GNOME, since the extension hooks private shell
# code. It needs a host with GNOME Shell, not a build container.
set -uo pipefail

REPO=$(cd "$(dirname "$0")/../.." && pwd)
SRC=$REPO/files/system/usr/share
UUID=redfox-dim@redfoxlabs.tech
DRIVER=driver@redfox-dim.test

WORK=$(mktemp -d "${TMPDIR:-/tmp}/redfox-dim-test.XXXXXX")
cleanup() {
    # Portals and gvfs may have mounted things in the runtime directory
    grep -F "$WORK" /proc/mounts | awk '{print $2}' | xargs -r -n1 fusermount -uz 2>/dev/null
    rm -rf "$WORK"
}
trap cleanup EXIT

EXT=$WORK/data/gnome-shell/extensions
mkdir -p "$EXT" "$WORK/config" "$WORK/cache" "$WORK/state" "$WORK/run" "$WORK/schemas"
chmod 700 "$WORK/run"
cp -r "$SRC/gnome-shell/extensions/$UUID" "$EXT/"
cp -r "$REPO/tests/redfox-dim/$DRIVER" "$EXT/"

MAJOR=$(gnome-shell --version | sed -E 's/[^0-9]*([0-9]+).*/\1/')
sed -i "s/SHELL_VERSION/$MAJOR/" "$EXT/$DRIVER/metadata.json"
# As the image build does
"$REPO/files/scripts/stamp-redfox-dim.sh" "$EXT/$UUID/metadata.json" "$MAJOR" || exit 1

cp "$SRC/glib-2.0/schemas/org.gnome.shell.extensions.redfox-dim.gschema.xml" "$WORK/schemas/"
glib-compile-schemas "$WORK/schemas"

run_shell() {
    local enabled="'$DRIVER'" monitors=(--virtual-monitor 1920x1200)
    [ "$1" = startup ] && enabled="'$DRIVER', '$UUID'"
    [ "$1" = mixed ] && monitors+=(--virtual-monitor 1600x1000)

    # A session of its own, so all of it can be killed however it ends up.
    REDFOX_DIM_TEST_PHASE=$1 REDFOX_DIM_TEST_RESULT=$WORK/$1.json \
    XDG_DATA_HOME=$WORK/data XDG_CONFIG_HOME=$WORK/config XDG_CACHE_HOME=$WORK/cache \
    XDG_STATE_HOME=$WORK/state XDG_RUNTIME_DIR=$WORK/run \
    GSETTINGS_SCHEMA_DIR=$WORK/schemas GSETTINGS_BACKEND=keyfile GVFS_DISABLE_FUSE=1 \
    setsid dbus-run-session -- bash -c "
        gsettings set org.gnome.shell enabled-extensions \"[$enabled]\"
        gsettings set org.gnome.shell disable-user-extensions false
        exec gnome-shell --headless --no-x11 --wayland-display=redfox-dim-test ${monitors[*]}
    " >"$WORK/$1.log" 2>&1 &
    local session=$!
    (sleep 90; kill -9 -- "-$session" 2>/dev/null) &
    local watchdog=$!
    wait "$session"
    kill "$watchdog" 2>/dev/null
    kill -9 -- "-$session" 2>/dev/null
    wait 2>/dev/null
}

status=0
for phase in main restart startup no-backlight mixed; do
    run_shell "$phase"
    [ -s "$WORK/$phase.json" ] || echo '[]' > "$WORK/$phase.json"

    if ! python3 "$REPO/tests/redfox-dim/report.py" "$WORK/$phase.json" ||
        { [ "$phase" = startup ] && grep -E "can't (mark|dim)" "$WORK/$phase.log"; }; then
        status=1
        echo "--- $phase log:"
        grep -v -E "dbus-daemon|libva info" "$WORK/$phase.log" | tail -30
    fi
done

[ "$status" = 0 ] && echo "All good." || echo "Failures above."
exit "$status"

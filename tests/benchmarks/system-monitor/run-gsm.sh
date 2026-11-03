#!/bin/bash
# GNOME System Monitor from a throwaway Fedora 44 container, drawn on the
# hidden rfbench display, seeing the host's processes.
exec podman run --rm --name rfbench-gsm --pid=host --userns=keep-id --security-opt label=disable \
  --device /dev/dri -e HOME=/tmp/h -e WAYLAND_DISPLAY=rfbench -e XDG_RUNTIME_DIR=/run/user/1000 -e GDK_BACKEND=wayland \
  -e DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus -v /run/user/1000/bus:/run/user/1000/bus \
  -v /run/user/1000/rfbench:/run/user/1000/rfbench -v /etc/machine-id:/etc/machine-id:ro -v /run/user/1000/at-spi:/run/user/1000/at-spi \
  rfbench-gsm bash -c 'mkdir -p /tmp/h; exec gnome-system-monitor'

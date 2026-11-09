#!/usr/bin/env bash
# Declares RedFox Dim compatible with the GNOME Shell being built into the image,
# because a shell won't load an extension that doesn't list its version. If a new
# GNOME has changed what the extension hooks, the extension logs an error and leaves
# the stock slider alone (tests/redfox-dim/run.sh shows whether it still works).
#
#   stamp-redfox-dim.sh [metadata.json] [shell major version]
set -euo pipefail

METADATA=${1:-/usr/share/gnome-shell/extensions/redfox-dim@redfoxlabs.tech/metadata.json}
MAJOR=${2:-$(rpm -q --qf '%{VERSION}' gnome-shell | cut -d. -f1)}

python3 - "$METADATA" "$MAJOR" <<'P'
import json, sys

path, major = sys.argv[1:]
with open(path) as f:
    metadata = json.load(f)
if major not in metadata["shell-version"]:
    metadata["shell-version"].append(major)
    with open(path, "w") as f:
        json.dump(metadata, f, indent=2)
        f.write("\n")
P

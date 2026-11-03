#!/usr/bin/bash
# Give Mailspring GNOME's Adwaita look. RedFox ships two theme packages,
# RedFox Adwaita Light and Dark, and Mailspring's "Automatic" theme (its
# default) switches between them as GNOME switches between light and dark.
#
# The themes are copied into Mailspring's own packages folder each login, so
# fixes arrive with image updates. A light or dark theme the user picked in
# Mailspring is left alone.

set -euo pipefail

APP=com.getmailspring.Mailspring
SRC=/usr/share/redfox/mailspring
DIR="$HOME/.var/app/$APP/config/Mailspring"
CONFIG="$DIR/config.json"

[ -d "$SRC" ] || exit 0
flatpak info "$APP" &> /dev/null || [ -d "$DIR" ] || exit 0

mkdir -p "$DIR/packages"
for variant in light dark; do
    name="ui-redfox-adwaita-$variant"
    stage="$(mktemp -d "$DIR/packages/.$name.XXXXXX")"
    cp -r "$SRC/$name/." "$stage/"
    cp "$SRC/adwaita-variables.less" "$stage/styles/adwaita-variables.inc"
    cp "$SRC/adwaita.less" "$stage/styles/adwaita.less"
    cp "$SRC/adwaita-icons.less" "$stage/styles/adwaita-icons.less"
    cp "$SRC/email-frame.less" "$stage/styles/email-frame.less"
    rm -rf "$DIR/packages/$name"
    mv "$stage" "$DIR/packages/$name"
done

# The companion plugin: window buttons follow GNOME's button-layout setting.
plugin=redfox-gnome-integration
if [ -d "$SRC/$plugin" ]; then
    stage="$(mktemp -d "$DIR/packages/.$plugin.XXXXXX")"
    cp -r "$SRC/$plugin/." "$stage/"
    rm -rf "$DIR/packages/$plugin"
    mv "$stage" "$DIR/packages/$plugin"
fi

python3 - "$CONFIG" <<'PY'
import json, os, sys
path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    # Mailspring writes this template on first start; match it, plus ours.
    config = {"*": {"env": "production", "core": {"themes": ["ui-light"], "disabledPackages": [
        "message-view-on-github", "personal-level-indicators", "phishing-detection",
        "nylas-private-salesforce", "github-contact-card", "keybase",
        "composer-markdown", "composer-scheduler", "composer-mail-merge"]}}}
except (OSError, ValueError):
    sys.exit(0)  # unreadable or hand-broken file: leave it for the user
appearance = config.setdefault("*", {}).setdefault("core", {}).setdefault("appearance", {})
changed = False
for key, theme in (("lightThemeName", "ui-redfox-adwaita-light"), ("darkThemeName", "ui-redfox-adwaita-dark")):
    if key not in appearance:
        appearance[key] = theme
        changed = True
if changed:
    tmp = path + ".redfox-tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)
    print("Mailspring's automatic theme now uses RedFox Adwaita Light and Dark.")
PY

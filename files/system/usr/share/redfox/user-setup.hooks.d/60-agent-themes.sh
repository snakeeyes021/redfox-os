#!/usr/bin/bash
# Terminal agents need a dark theme in a dark terminal and a light one in
# VS Code's (light) terminal. Claude Code's "auto" theme follows the
# terminal's background, so make that the default. A theme the user picked
# is left alone.

set -euo pipefail

CLAUDE_SETTINGS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json"

if command -v claude &> /dev/null || [ -d "$(dirname "$CLAUDE_SETTINGS")" ]; then
    python3 - "$CLAUDE_SETTINGS" <<'PY'
import json, os, sys
path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as f:
        settings = json.load(f)
except FileNotFoundError:
    settings = {}
except (OSError, ValueError):
    sys.exit(0)  # unreadable or hand-broken file: leave it for the user
if "theme" in settings:
    sys.exit(0)
settings["theme"] = "auto"
os.makedirs(os.path.dirname(path), exist_ok=True)
tmp = path + ".redfox-tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")
os.replace(tmp, path)
print("Claude Code theme set to auto (follows the terminal's light/dark background).")
PY
fi

#!/usr/bin/python3
"""Builds RedFox's Starship prompt themes from Starship's official presets.

Reads assets/starship/presets/*.toml (Starship's own preset files, ISC
licence, see presets/LICENSE) and writes files/system/usr/share/redfox/
starship/themes/: one .toml per preset, plus themes.tsv, the list that
redfox-terminal and RedFox Hub read (id, name, file, whether it uses Nerd
Font symbols). In the presets that show Starship's `os` module, the fox
replaces the symbol for the systems Starship can report RedFox as (it reads
/etc/os-release; RedFox's ID isn't one it knows, so it falls back to Fedora).

The fox is FOX below: RedFox's fox-face symbol, U+10F000 in the RedFox
Symbols font (assets/fox-glyph/), which has no colour of its own and takes
the preset's colours. None leaves Starship's own symbols. RedFox's own prompt
(files/system/usr/share/redfox/starship.toml) isn't touched: it keeps its 🦊.

Usage: assets/starship/make-themes.py   (from the repository root)
"""
import os
import re

# RedFox's fox face in the RedFox Symbols font (fonts/redfox-symbols).
FOX = "\U0010F000"
STARSHIP_VERSION = "1.27.0"
# The os.symbols entries the fox replaces (or adds).
FOX_KEYS = ["Fedora", "Linux", "Unknown", "Bazzite"]

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "assets", "starship", "presets")
OUT = os.path.join(ROOT, "files", "system", "usr", "share", "redfox", "starship", "themes")
REDFOX = "/usr/share/redfox/starship.toml"
THEMES_DIR = "/usr/share/redfox/starship/themes"

# id: display name, as on starship.rs/presets.
PRESET_NAMES = {
    "bracketed-segments": "Bracketed Segments",
    "catppuccin-powerline": "Catppuccin Powerline",
    "gruvbox-rainbow": "Gruvbox Rainbow",
    "jetpack": "Jetpack",
    "nerd-font-symbols": "Nerd Font Symbols",
    "no-empty-icons": "No Empty Icons",
    "no-nerd-font": "No Nerd Fonts",
    "no-runtime-versions": "No Runtime Versions",
    "pastel-powerline": "Pastel Powerline",
    "plain-text-symbols": "Plain Text Symbols",
    "pure-preset": "Pure",
    "tokyo-night": "Tokyo Night",
}


def uses_nerd_font(text):
    """Nerd Font symbols live in Unicode's private-use areas."""
    return any(0xE000 <= ord(c) <= 0xF8FF or ord(c) >= 0xF0000 for c in text)


def shows_os(text):
    """Whether the preset's prompt shows the os module."""
    section = re.search(r"(?ms)^\[os\]\n(.*?)(?=^\[|\Z)", text)
    return bool(section) and re.search(r"(?m)^disabled\s*=\s*false", section.group(1)) is not None


def with_fox(text):
    """The preset with the fox as the symbol for FOX_KEYS, keeping each
    entry's spacing (some presets put a space after their symbols)."""
    match = re.search(r"(?ms)^\[os\.symbols\]\n(.*?)(?=^\[|\Z)", text)
    if not match:
        return text.rstrip("\n") + "\n\n[os.symbols]\n" + "".join(
            f'{key} = "{FOX} "\n' for key in FOX_KEYS)
    body = match.group(1)
    suffix = " " if re.search(r'(?m)^Linux = ".* "$', body) else ""
    for key in FOX_KEYS:
        line = f'{key} = "{FOX}{suffix}"'
        if re.search(rf"(?m)^{key} = ", body):
            body = re.sub(rf'(?m)^{key} = ".*"$', lambda _m: line, body)
        else:
            body = body.rstrip("\n") + "\n" + line + "\n"
    return text[:match.start(1)] + body + text[match.end(1):]


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = [
        ("redfox", "RedFox", REDFOX, "no"),
        ("starship", "Starship's Default", f"{THEMES_DIR}/starship.toml", "no"),
    ]
    with open(os.path.join(OUT, "starship.toml"), "w", encoding="utf-8") as f:
        f.write("# Starship's own defaults: no settings of RedFox's.\n")
    for preset_id, name in PRESET_NAMES.items():
        with open(os.path.join(SRC, f"{preset_id}.toml"), encoding="utf-8") as f:
            text = f.read()
        header = (f"# Starship's \"{name}\" preset (starship.rs/presets), from Starship "
                  f"{STARSHIP_VERSION}.\n# ISC licence, Starship Contributors: see LICENSE "
                  "in this folder.\n")
        if FOX and shows_os(text):
            text = with_fox(text)
            header += "# RedFox: the fox is the OS symbol.\n"
        with open(os.path.join(OUT, f"{preset_id}.toml"), "w", encoding="utf-8") as f:
            f.write(header + text)
        rows.append((preset_id, name, f"{THEMES_DIR}/{preset_id}.toml",
                     "yes" if uses_nerd_font(text) else "no"))
    with open(os.path.join(SRC, "LICENSE"), encoding="utf-8") as f:
        licence = f.read()
    with open(os.path.join(OUT, "LICENSE"), "w", encoding="utf-8") as f:
        f.write("The Starship presets in this folder come from Starship "
                f"(https://github.com/starship/starship, {STARSHIP_VERSION}):\n\n" + licence)
    with open(os.path.join(OUT, "themes.tsv"), "w", encoding="utf-8") as f:
        f.write("# id\tname\tfile\tnerd font\n")
        for row in rows:
            f.write("\t".join(row) + "\n")
    print(f"{len(rows)} themes in {OUT}")


if __name__ == "__main__":
    main()

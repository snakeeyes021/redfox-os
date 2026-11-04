*Want a different desktop?* `redfox-layout list` shows the layouts (RedFox, GNOME, Ubuntu, Cal, Wash, Nostalgia); `redfox-layout set cal` switches without logging out
It is **always** better to install packages in a Distrobox than to layer them with rpm-ostree. `ujust distrobox` makes it easy
*Need a Python environment?* `uv` and `pixi` are preinstalled: `uv venv`, or `uv run --with <package>` for a one-off
*Update break something?* Pick the previous version in the boot menu, or run `rpm-ostree rollback` and reboot
*Command-line tools* are best installed with Homebrew: `brew install <tool>`
*Software packs:* `ujust install-productivity`, `install-creative`, `install-music`, `install-dev` and more install curated app sets
*Playing an instrument?* Midikeep records everything you play over MIDI; `midikeep list` shows your takes

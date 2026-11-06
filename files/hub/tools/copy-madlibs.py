#!/usr/bin/env python3
"""Make the blind copy pass's madlibs list and ID map for RedFox Hub.

    python3 files/hub/tools/copy-madlibs.py OUT_DIR

Writes OUT_DIR/copy-madlibs.md (what each string is for, never its current
wording, with a blank line for new text) and OUT_DIR/copy-map.json (each ID's
current text and where it lives, so answers can be applied by ID).

Hub's own strings come from redfox_hub/strings.py. The rest comes from where
Hub shows it from: the Manual pages, the software catalog, the layouts and
the graphics images. Run from the repo root (or anywhere: paths are found
from this file).
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
HUB = REPO / "files/hub"
sys.path.insert(0, str(HUB / "src"))

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from redfox_hub import manual  # noqa: E402
from redfox_hub.strings import ENTRIES, VOICE  # noqa: E402

ALL = "--all" in sys.argv  # every string, not only the ones with voice
sys.path.insert(0, str(Path(__file__).resolve().parent))
from copy_context import CONTEXT  # noqa: E402

SHOTS_URL = "https://redmax.taila6a47f.ts.net:8413/img/copy-voice/"

# Where the launcher, store and password-prompt strings live (not in Python).
FILE_STRINGS = {
    "H-001": ("files/hub/data/tech.redfoxlabs.Hub.desktop", "Name="),
    "H-002": ("files/hub/data/tech.redfoxlabs.Hub.desktop", "GenericName="),
    "H-003": ("files/hub/data/tech.redfoxlabs.Hub.desktop", "Comment="),
    "H-004": ("files/hub/data/tech.redfoxlabs.Hub.desktop", "Keywords="),
    "H-005": ("files/hub/data/tech.redfoxlabs.Hub.desktop", "Name=Updates"),
    "H-006": ("files/hub/data/tech.redfoxlabs.Hub.desktop", "Name=Choose a Layout"),
    "H-007": ("files/hub/data/tech.redfoxlabs.Hub.desktop", "Name=Manual"),
    "H-008": ("files/hub/data/tech.redfoxlabs.Hub.metainfo.xml", "<summary>"),
    "H-009": ("files/hub/data/tech.redfoxlabs.Hub.metainfo.xml", "<p>RedFox Hub"),
    "H-010": ("files/system/usr/share/polkit-1/actions/tech.redfoxlabs.Hub.policy", "<description>"),
    "H-011": ("files/system/usr/share/polkit-1/actions/tech.redfoxlabs.Hub.policy", "<message>"),
}

# What each Manual page's title, summary and blocks are for. Keys are
# "<slug>-title", "<slug>-summary" and "<slug>-<block number>", numbered the
# way manual.blocks() reads the page (code blocks are commands, not copy).
MANUAL_JOBS = {
    "how-it-works-title": "Title of the help page that explains the basic idea of the system: one image, replaced whole.",
    "how-it-works-summary": "One sentence under that title summing up the idea, and that your own files and apps are separate.",
    "how-it-works-1": "Heading over the explanation of the whole-system image.",
    "how-it-works-2": "Explains what the system is built on, and that it's installed and updated as one piece rather than package by package.",
    "how-it-works-3": "Explains where the image lives, that it's read-only, and why that's safe.",
    "how-it-works-4": "Heading over the list of what belongs to the user rather than the system.",
    "how-it-works-5": "List item: your home folder (and where it really lives) is never touched by updates.",
    "how-it-works-6": "List item: apps from the store, Homebrew and containers sit outside the image and survive updates; links to the apps page.",
    "how-it-works-7": "List item: the machine's settings folder keeps your changes and merges them with the defaults.",
    "how-it-works-8": "Heading over what this means in everyday use.",
    "how-it-works-9": "List item: updates happen quietly and apply on restart; links to the updates page.",
    "how-it-works-10": "List item: a bad update can be undone, the old system is still there.",
    "how-it-works-11": "List item: apps aren't installed the usual Fedora way; where each kind of app comes from instead.",
    "how-it-works-12": "Heading over the three versions of the system.",
    "how-it-works-13": "Introduces the list of system versions, which depend on the graphics card.",
    "how-it-works-14": "List item: the version for Intel and AMD graphics (keeps its technical name).",
    "how-it-works-15": "List item: the version for newer NVIDIA cards (keeps its technical name).",
    "how-it-works-16": "List item: the version for older NVIDIA cards (keeps its technical name).",
    "how-it-works-17": "Introduces a terminal command that shows which version you're running.",
    "updates-title": "Title of the help page about updates and undoing them.",
    "updates-summary": "One sentence: updates are daily, apply on restart, and the previous system is kept.",
    "updates-1": "Heading over how the daily updates work.",
    "updates-2": "Explains the daily download, that nothing changes until you restart, and that there's no hurry.",
    "updates-3": "Explains how to update right away from the app, what that covers, and the restart afterwards.",
    "updates-4": "Heading over undoing an update.",
    "updates-5": "Says every update keeps the previous system, and introduces the ways to go back.",
    "updates-6": "List item: going back once from the menu at startup, and how to get that menu to show.",
    "updates-7": "List item: going back from the app's updates page.",
    "updates-8": "List item: going back from a terminal (a command follows).",
    "updates-10": "Explains that going back only changes the system, not your files, and that the next update moves forward again.",
    "updates-11": "Heading over the two update channels.",
    "updates-12": "Introduces the two channels.",
    "updates-13": "List item: the stable channel, the default, gets changes after they've been tried.",
    "updates-14": "List item: the unstable channel, built daily, gets changes first with some risk.",
    "updates-15": "Introduces a terminal command that shows your channel and the kept systems.",
    "updates-17": "Introduces the terminal commands that switch channel.",
    "updates-19": "Heading over going back further than one update.",
    "updates-20": "Explains picking an older build by date or change, and introduces the command that lists builds.",
    "updates-22": "Explains switching to one of those builds, and that it then stays put until you follow a channel again.",
    "updates-23": "Heading over the graphics-card versions of the system.",
    "updates-24": "Introduces the three versions, one per kind of graphics.",
    "updates-25": "List item: the version for Intel and AMD graphics.",
    "updates-26": "List item: the version for newer NVIDIA cards.",
    "updates-27": "List item: the version for older NVIDIA cards.",
    "updates-28": "Explains that each version follows either channel, and how to change version in the app or a terminal.",
    "updates-30": "A warning to pick the version that matches your card, and what to do if the screen goes blank.",
    "updates-31": "Heading over trying developers' work in progress.",
    "updates-32": "Explains what these test builds are, where they appear in the app, that they're unsupported, and how to get back.",
    "installing-apps-title": "Title of the help page about where to get software.",
    "installing-apps-summary": "One sentence: which source to use for desktop apps, command-line tools and everything else, and the last resort.",
    "installing-apps-1": "Heading over getting desktop apps from the store.",
    "installing-apps-2": "Explains the store, where its apps come from, and how they run.",
    "installing-apps-3": "Points to RedFox's ready-made sets of apps in the app.",
    "installing-apps-4": "Introduces the terminal command for installing a store app.",
    "installing-apps-6": "Heading over getting command-line tools from Homebrew.",
    "installing-apps-7": "Explains what Homebrew is for and that it doesn't touch the system (a command follows).",
    "installing-apps-9": "Says the updates keep Homebrew tools up to date too.",
    "installing-apps-10": "Heading over running other Linux systems' software in a container.",
    "installing-apps-11": "Explains what that container tool does and when to use it (a command follows).",
    "installing-apps-13": "Explains installing inside the container and putting its apps in the app grid.",
    "installing-apps-14": "Points to the app that does the same with buttons.",
    "installing-apps-15": "Heading over the last-resort way of adding a package to the system itself.",
    "installing-apps-16": "Explains what adding a package to the system does and when it's the only option.",
    "installing-apps-17": "Introduces the list of downsides.",
    "installing-apps-18": "List item: downside, every update gets slower.",
    "installing-apps-19": "List item: downside, it can block updates.",
    "installing-apps-20": "List item: downside, it needs a restart.",
    "installing-apps-22": "Introduces the commands that list and remove what you added.",
    "dev-environments-title": "Title of the help page about giving a team identical developer setups.",
    "dev-environments-summary": "One sentence recommending a container described in the project for a team that needs the same tools.",
    "dev-environments-1": "Heading over development containers.",
    "dev-environments-2": "Explains what a development container is and how the editor uses it.",
    "dev-environments-3": "Says the system already has the editor, the container tools and the editor extension needed.",
    "dev-environments-4": "Heading over setting one up, step by step.",
    "dev-environments-5": "Step: open the project in the editor.",
    "dev-environments-6": "Step: run the editor command that adds the container files.",
    "dev-environments-7": "Step: choose a starting point and the language version.",
    "dev-environments-8": "Step: reopen in the container; the first start is slow, later ones quick.",
    "dev-environments-9": "Step: commit the container folder so collaborators share it.",
    "dev-environments-10": "Explains where the language version is set and how to change it.",
    "dev-environments-11": "Explains what collaborators need and what happens when they open the project.",
    "dev-environments-12": "Heading over a common container-tool permission error.",
    "dev-environments-13": "Explains why it happens on a new system and the one-time fix (log out and in).",
    "dev-environments-15": "Heading over the simpler option for a personal setup.",
    "dev-environments-16": "Explains when a personal long-lived container is enough (a command follows).",
    "dev-environments-18": "Explains installing the language version inside it, kept apart from the system.",
    "python-title": "Title of the help page about Python on this system.",
    "python-summary": "One sentence naming the two Python tools that come with the system and what each is for.",
    "python-1": "Heading over why not to install packages into the system's Python.",
    "python-2": "Explains that the system's Python is read-only and used by the system's own tools, so installing into it doesn't work.",
    "python-3": "Heading over the tool for ordinary Python projects.",
    "python-4": "Explains what that tool does (a command follows).",
    "python-6": "Explains the project files it keeps and how collaborators get the same packages.",
    "python-7": "Introduces the command for a particular Python version in one project.",
    "python-9": "Introduces the command for a plain virtual environment in the current folder.",
    "python-11": "Introduces the command for a Python command-line tool installed just for you.",
    "python-13": "Introduces the command for running a one-off script that needs a package.",
    "python-15": "Heading over the tool for conda-style projects.",
    "python-16": "Explains what that tool installs and when to use it (a command follows).",
    "python-18": "Explains where its globally installed tools go.",
    "python-19": "Heading over Python inside a development container.",
    "python-20": "Points to the team-setups page for pinning Python the same way.",
    "layouts-title": "Title of the help page about desktop layouts.",
    "layouts-summary": "One sentence: there are six layouts, and you can switch at any time without logging out.",
    "layouts-1": "Heading over how to pick one.",
    "layouts-2": "Explains where in the app to pick a layout, that it applies at once, and that apps stay open.",
    "layouts-3": "Heading over the list of the six layouts.",
    "layouts-4": "List item: the RedFox layout and where it puts the dock.",
    "layouts-5": "List item: the GNOME layout, plain GNOME, and that it's the default.",
    "layouts-6": "List item: the Ubuntu layout and its always-visible side dock.",
    "layouts-7": "List item: the Cal layout, its bottom dock and window buttons.",
    "layouts-8": "List item: the Wash layout's centred taskbar.",
    "layouts-9": "List item: the Nostalgia layout's left-aligned taskbar.",
    "layouts-10": "Explains the two extra dock options below the layout cards.",
    "layouts-11": "Heading over switching layouts from a terminal (a command follows).",
    "layouts-13": "Says which names the command expects.",
    "getting-help-title": "Title of the help page about what to do when something goes wrong.",
    "getting-help-summary": "One sentence: finding out what went wrong, and where to report it.",
    "getting-help-1": "Heading over the first things to try.",
    "getting-help-2": "List item: if it began after an update, go back and see; links to the updates page.",
    "getting-help-3": "List item: if it's one store app, it's that app's developers to ask, not this system's.",
    "getting-help-4": "Heading over reading the system's logs.",
    "getting-help-5": "Points to the logs app and what it shows.",
    "getting-help-6": "Introduces the terminal command for errors since this start.",
    "getting-help-8": "Introduces the command for errors from the previous start, after a crash or failed update.",
    "getting-help-10": "Introduces the command for one service's messages, such as the automatic update.",
    "getting-help-12": "Introduces the command for your own session's messages.",
    "getting-help-14": "Heading over reporting a problem.",
    "getting-help-15": "Says where to report problems (a web address follows).",
    "getting-help-16": "Explains what a good report includes, and introduces the command that shows the system you're running.",
    "getting-help-18": "Finishes that sentence: also paste error lines from the logs.",
}

# Plain names for the modules, for "used in" notes.
AREAS = {
    "app": "About dialog", "window": "sidebar and page headers", "welcome": "Welcome",
    "apps": "Apps", "updates": "Updates", "settings": "Settings", "manual": "Manual",
    "host": "error messages",
}

GRAPHICS_JOBS = {
    "redfox-os": "computers with Intel or AMD graphics",
    "redfox-os-nvidia": "newer NVIDIA cards (GTX 16 series, RTX 20 series and later)",
    "redfox-os-nvidia-legacy": "older NVIDIA cards (GTX 10 series and earlier)",
}


def usages():
    """ID -> ["file:line", ...] for every s("H-xxx") in Hub's code."""
    found = {}
    for path in sorted((HUB / "src/redfox_hub").glob("*.py")):
        if path.name == "strings.py":
            continue
        for n, line in enumerate(path.read_text().splitlines(), 1):
            for id_ in re.findall(r"""s\(["'](H-\d{3})["']""", line):
                found.setdefault(id_, []).append(f"{path.relative_to(REPO)}:{n}")
    return found


def strings_line(id_):
    path = HUB / "src/redfox_hub/strings.py"
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if f'("{id_}",' in line:
            return f"{path.relative_to(REPO)}:{n}"
    return None


def file_line(rel, needle):
    for n, line in enumerate((REPO / rel).read_text().splitlines(), 1):
        if needle in line:
            return f"{rel}:{n}"
    return rel


def entry(id_, kind, job, budget, extra=""):
    job = job.rstrip(".")
    parts = [f"**{id_}**", f"*{kind}*", job if job.endswith(("…", ")")) else job + "."]
    if budget:
        parts.append(budget)
    if extra:
        parts.append(extra)
    return "- " + " · ".join(parts) + "\n  →\n"


def rich_entry(id_, kind, budget, extra):
    c = CONTEXT[id_]
    shots = ", ".join(f"[{f}]({SHOTS_URL}{f})" for f in c["shots"]) or "none (not shown inside Hub)"
    head = [f"**{id_}**", f"*{kind}*"] + ([budget] if budget else []) + ([extra] if extra else [])
    return ("- " + " · ".join(head) + "\n"
            f"  - **Where:** {c['where']} Screenshots: {shots}.\n"
            f"  - **When they see it:** {c['when']}\n"
            f"  - **What they need then:** {c['needs']}\n"
            f"  - **What it must get across:** {c['across']}\n"
            "  →\n")


def main():
    out = Path([a for a in sys.argv[1:] if not a.startswith("--")][0])
    out.mkdir(parents=True, exist_ok=True)
    used = usages()
    md = ["# RedFox Hub: copy, blind pass\n",
          "Write your text after each →. Leave a line blank to keep the current text for now. "
          "Don't change the IDs.\n"
          "`{name}`-style placeholders are filled in by the app; keep them if you use that fact.\n"]
    if not ALL:
        md.append("\nOnly the words with some voice are here: the welcome, the hero lines, the store text. "
                  "Everything else (buttons, headings, labels, explanations, error details, the Manual's pages, "
                  "the app catalog) keeps its current text. Any of it can still be changed later: "
                  "\"make the thing that says abc say xyz\".\n")
    mapping = {}
    counts = {}

    # Hub's own strings, grouped by screen in reading order.
    screen = None
    for id_, scr, kind, job, budget, _short, text in ENTRIES:
        if not ALL and id_ not in VOICE:
            continue
        if scr != screen:
            md.append(f"\n## {scr}\n")
            screen = scr
        where = used.get(id_, [])
        extra = ""
        if len(where) > 1:
            places = {}
            for w in where:
                area = AREAS.get(Path(w.split(":")[0]).stem, Path(w).stem)
                places[area] = places.get(area, 0) + 1
            extra = "used in: " + ", ".join(
                area + (f" ×{n}" if n > 1 else "") for area, n in places.items())
        md.append(rich_entry(id_, kind, budget, extra) if not ALL and id_ in CONTEXT
                  else entry(id_, kind, job, budget, extra))
        counts[scr] = counts.get(scr, 0) + 1
        source = [file_line(*FILE_STRINGS[id_])] if id_ in FILE_STRINGS else []
        mapping[id_] = {"text": text, "defined": strings_line(id_),
                        "used": source + where}

    if not ALL:
        retired(md)
        return finish(out, md, mapping, counts)

    # Optional, long: the Manual, one entry per block.
    manual.MANUAL_DIR = HUB / "data/manual"
    md.append("\n## Manual pages *(optional, long)*\n")
    md.append("One entry per heading, paragraph or list item. Commands in grey boxes aren't copy and aren't listed. "
              "Keep `[links](manual:…)` and `**bold**` markers if you want them; Markdown is fine.\n")
    count = 0
    for page in manual.load_pages():
        path = next(manual.MANUAL_DIR.glob(f"*-{page.slug}.md"))
        md.append(f"\n### Manual: {page.slug}\n")
        parts = [("title", "page title", page.title), ("summary", "page summary", page.summary)]
        parts += [(str(n), kind, text) for n, (kind, text, _m) in enumerate(manual.blocks(page.body), 1)
                  if kind != "code"]
        for part, kind, text in parts:
            key = f"{page.slug}-{part}"
            id_ = f"H-M-{key}"
            md.append(entry(id_, {"paragraph": "paragraph", "item": "list item",
                                  "heading": "section heading"}.get(kind, kind),
                            MANUAL_JOBS[key], "wraps freely" if kind in ("paragraph", "item") else ""))
            mapping[id_] = {"text": text, "used": [str(path.relative_to(REPO))]}
            count += 1
    counts["Manual pages (optional)"] = count

    # Optional: the software catalog's packs and app summaries (Apps page).
    catalog = yaml.safe_load((REPO / "files/system/usr/share/redfox/software.yaml").read_text())
    items = {i["id"]: i for i in catalog.get("items", [])}
    md.append("\n## Apps page: packs and app lines *(optional, long)*\n")
    md.append("From the software catalog (`software.yaml`). App names are left as they are.\n")
    count = 0
    for pack in catalog["packs"]:
        if pack.get("hidden") or not pack.get("items"):
            continue
        names = [items.get(i, {}).get("name", i) for i in pack["items"]][:4]
        sample = ", ".join(names) + ("…" if len(pack["items"]) > 4 else "")
        for field, kind, job in (
                ("name", "group heading", f"Name of the software set that holds {sample}"),
                ("description", "group description", f"One line under that set's name saying what kind of apps are in it ({sample})")):
            id_ = f"H-P-{pack['id']}-{field}"
            md.append(entry(id_, kind, job, "≤ 3 words" if field == "name" else "≤ 15 words"))
            mapping[id_] = {"text": pack.get(field, ""), "used": [f"files/system/usr/share/redfox/software.yaml (packs: {pack['id']}.{field})"]}
            count += 1
    seen = set()
    for pack in catalog["packs"]:
        if pack.get("hidden"):
            continue
        for item_id in pack.get("items", []):
            if item_id in seen or item_id not in items:
                continue
            seen.add(item_id)
            item = items[item_id]
            id_ = f"H-A-{item.get('id', item_id)}"
            md.append(entry(id_, "row subtitle", f"One line under {item['name']}, saying what the app is for", "≤ 12 words"))
            mapping[id_] = {"text": item.get("summary", ""), "used": [f"files/system/usr/share/redfox/software.yaml (items: {item_id}.summary)"]}
            count += 1
    counts["Apps catalog (optional)"] = count

    # The layouts' one-line descriptions (Layout page cards; names are Matt's).
    layouts = json.loads(subprocess.run(
        [sys.executable, str(REPO / "files/system/usr/bin/redfox-layout"), "list", "--json"],
        capture_output=True, text=True).stdout or '{"layouts": []}')["layouts"]
    md.append("\n## Layout page: the layouts' lines\n")
    md.append("Under each layout's picture and name. The names are already decided.\n")
    for layout in layouts:
        id_ = f"H-L-{layout['id']}"
        md.append(entry(id_, "card text", f"One line under the {layout['title']} layout's name saying where it puts the dock, top bar or taskbar", "≤ 15 words; wraps to 3 lines"))
        mapping[id_] = {"text": layout["description"], "used": ["files/system/usr/bin/redfox-layout (LAYOUTS)"]}
    counts["Layout cards"] = len(layouts)

    # The graphics variants (Updates › System Image dropdown).
    md.append("\n## Updates: the graphics variants\n")
    md.append("The dropdown's entries and the line under it. NVIDIA is a name; the rest is copy.\n")
    images = json.loads(subprocess.run(
        ["bash", str(REPO / "files/system/usr/bin/redfox-rollback-helper"), "--json", "images"],
        capture_output=True, text=True).stdout or '{"images": []}')["images"]
    for image in images:
        for field, kind, job, budget in (
                ("name", "dropdown entry", f"Name of the system variant for {GRAPHICS_JOBS[image['id']]}", "≤ 2 words"),
                ("description", "row subtitle", f"Under the dropdown when that variant is picked: which graphics cards it's for. Fact: it's for {GRAPHICS_JOBS[image['id']]}", "≤ 8 words")):
            id_ = f"H-G-{image['id']}-{field}"
            md.append(entry(id_, kind, job, budget))
            mapping[id_] = {"text": image[field], "used": [f"files/system/usr/bin/redfox-rollback-helper (image_{field})"]}
    counts["Graphics variants"] = len(images) * 2

    finish(out, md, mapping, counts)


def retired(md):
    """The strings dropped from the pass, one line each: they keep their text."""
    md.append("\n## Retired from this pass (they keep their current text)\n")
    md.append("Plain labels, headings, buttons and explanations. Listed so nothing goes missing; "
              "say \"make the thing that says abc say xyz\" for any of them.\n\n")
    screen = None
    for id_, scr, kind, _job, _budget, short, _text in ENTRIES:
        if id_ in VOICE:
            continue
        if scr != screen:
            md.append(f"\n*{scr}*\n\n")
            screen = scr
        md.append(f"- {id_} · {kind} · {short}\n")
    md.append("\n*Text from elsewhere*\n\n"
              "- H-M-…: the Manual's seven pages (titles, summaries, every paragraph)\n"
              "- H-P-… and H-A-…: the Apps catalog's pack names and descriptions, and each app's one-line description\n"
              "- H-L-…: the line under each layout's card\n"
              "- H-G-…: the graphics variants' names and descriptions\n")


def finish(out, md, mapping, counts):
    md.append("\n## Not covered in this pass\n")
    md.append("- The `ujust switch-image` prompts and other `redfox-rollback-helper` terminal text.\n"
              "- The terminal banner (MOTD) and its tips.\n"
              "- Messages that come straight from a system tool and are shown as they are "
              "(the last line of a failed command in a toast, Midikeep's \"folder changed\" sentence, "
              "error text from GitHub or the registry).\n"
              "- The app's command-line `--help` text (developer-only).\n")

    (out / "copy-madlibs.md").write_text("".join(md))
    (out / "copy-map.json").write_text(json.dumps(mapping, indent=2, ensure_ascii=False) + "\n")
    for screen_name, n in counts.items():
        print(f"{n:4}  {screen_name}")
    print(f"{sum(counts.values()):4}  total -> {out / 'copy-madlibs.md'}")


if __name__ == "__main__":
    main()

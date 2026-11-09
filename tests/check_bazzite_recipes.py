#!/usr/bin/env python3
"""Flags when Bazzite changes a `ujust` recipe that RedFox has its own version of.

RedFox runs some of Bazzite's recipes its own way, without their questions
(redfox-hardware, redfox-hardware-root, redfox-dedup, redfox-system-action).
tests/bazzite-recipes.json records a hash of each recipe as it was when
RedFox's version was written. When Bazzite changes one, this lists it, so
RedFox's version can be checked against the change and the hash updated.

  check_bazzite_recipes.py JUST_DIR            exit 1 if any recipe changed
  check_bazzite_recipes.py JUST_DIR --update   record the current hashes

JUST_DIR is Bazzite's /usr/share/ublue-os/just (CI reads it from the base
image). On GitHub it prints a warning annotation per changed recipe.
"""

import hashlib
import json
import os
import re
import sys
from pathlib import Path

RECORD = Path(__file__).with_name("bazzite-recipes.json")


def recipes(just_dir):
    """Every recipe's text (its first line and indented body), by name."""
    found = {}
    for path in sorted(Path(just_dir).glob("*.just")):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        i = 0
        while i < len(lines):
            match = re.match(r"^([A-Za-z0-9_-]+)(?:\s[^:]*)?:(?!=)", lines[i])
            if not match:
                i += 1
                continue
            body = [lines[i]]
            i += 1
            while i < len(lines) and (not lines[i].strip() or lines[i][0] in " \t"):
                body.append(lines[i])
                i += 1
            while body and not body[-1].strip():
                body.pop()
            found.setdefault(match.group(1), "\n".join(body))
    return found


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def main(argv):
    if len(argv) not in (2, 3) or (len(argv) == 3 and argv[2] != "--update"):
        print(__doc__, file=sys.stderr)
        return 2
    record = json.loads(RECORD.read_text())
    current = recipes(argv[1])
    if len(argv) == 3:
        for name in record["recipes"]:
            record["recipes"][name]["sha256"] = digest(current[name])
        RECORD.write_text(json.dumps(record, indent=2) + "\n")
        print(f"Recorded {len(record['recipes'])} recipes.")
        return 0
    changed = []
    for name, entry in record["recipes"].items():
        if name not in current:
            changed.append((name, "is gone from Bazzite", entry["ours"]))
        elif digest(current[name]) != entry["sha256"]:
            changed.append((name, "has changed in Bazzite", entry["ours"]))
    for name, what, ours in changed:
        message = f"ujust {name} {what}. Check RedFox's version in {ours}, then run " \
                  f"tests/check_bazzite_recipes.py <just dir> --update."
        print(f"::warning title=Bazzite recipe changed::{message}" if os.environ.get("GITHUB_ACTIONS")
              else message)
    if not changed:
        print(f"All {len(record['recipes'])} recipes are as recorded.")
    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

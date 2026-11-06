#!/usr/bin/env python3
"""Prints the results the test driver saved. Fails on a failed check, or if the
shell stopped before the driver got to the end."""
import json
import sys

with open(sys.argv[1]) as f:
    results = json.load(f)

for r in results:
    detail = f"  ({r['detail']})" if not r["ok"] and r["detail"] else ""
    print(("ok    " if r["ok"] else "FAIL  ") + r["name"] + detail)

finished = bool(results) and results[-1]["name"] == "finished"
if not finished:
    print("FAIL  the shell stopped before the tests finished")

sys.exit(0 if finished and all(r["ok"] for r in results) else 1)

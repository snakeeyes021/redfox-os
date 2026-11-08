#!/usr/bin/env bash
# RedFoxOS graphics check (Linux).
#
#   curl -sL https://raw.githubusercontent.com/snakeeyes021/redfox-os/main/extras/identify_gpu.sh | bash
#
# Lists this computer's display devices and says which RedFoxOS download
# suits them, with a link to it. It reads only each display device's PCI
# vendor and device id. It downloads RedFoxOS's graphics rules
# (files/system/usr/share/redfox/gpu-rules.json, the same rules the download
# page and RedFox Hub's "(Recommended)" use) and decides here; nothing about
# this computer is sent anywhere. The link carries the ids after a "#", which
# browsers keep to themselves, so opening it doesn't send them either.
# If the rules can't be downloaded, it prints a code to paste into the
# download page instead. The Windows version is identify_gpu.ps1.
#
# For tests: RFX_DEVICES="8086:46a6 10de:1c03" stands in for the computer's
# devices, and RFX_RULES_FILE=path reads the rules from a file.
set -euo pipefail

PAGE="https://redfoxlabs.tech/download/"
RULES_URLS=(
    "https://raw.githubusercontent.com/snakeeyes021/redfox-os/main/files/system/usr/share/redfox/gpu-rules.json"
    "https://raw.githubusercontent.com/snakeeyes021/redfox-os/unstable/files/system/usr/share/redfox/gpu-rules.json"
)

ids=()
if [ -n "${RFX_DEVICES+set}" ]; then
    read -r -a ids <<< "${RFX_DEVICES}"
else
    for dev in /sys/bus/pci/devices/*; do
        [ -r "$dev/class" ] || continue
        case "$(cat "$dev/class")" in 0x03*) ;; *) continue ;; esac # display controllers
        vendor="$(cat "$dev/vendor")"
        device="$(cat "$dev/device")"
        ids+=("${vendor#0x}:${device#0x}")
    done
fi

if [ "${#ids[@]}" -eq 0 ]; then
    echo "No graphics device found."
else
    echo "Graphics found:"
    for id in "${ids[@]}"; do
        name=""
        if [ -z "${RFX_DEVICES+set}" ] && command -v lspci >/dev/null 2>&1; then
            name="$(lspci -d "$id" 2>/dev/null | head -n1 | cut -d' ' -f2-)"
        fi
        echo "  ${id}${name:+  ${name}}"
    done
fi
echo

code="RFX1 ${ids[*]:-none}"
link="${PAGE}#gpu=${code// /+}"

rules=""
if [ -n "${RFX_RULES_FILE:-}" ]; then
    rules="$(cat "$RFX_RULES_FILE" 2>/dev/null)" || rules=""
else
    for url in "${RULES_URLS[@]}"; do
        if command -v curl >/dev/null 2>&1; then
            rules="$(curl -fsSL --max-time 15 "$url" 2>/dev/null)" && break
        elif command -v wget >/dev/null 2>&1; then
            rules="$(wget -qO- --timeout=15 "$url" 2>/dev/null)" && break
        fi
        rules=""
    done
fi

# The decision, the same way the download page makes it (download/gpu-rules.js
# on redfoxlabs.tech): each device gets the first class it matches, then the
# first rule whose classes all fit wins. Prints the image id, then the reason,
# then "hybrid" or nothing.
decide() {
    python3 -c '
import json, sys
rules = json.loads(sys.stdin.read())
have = set()
for pair in sys.argv[1:]:
    vendor, device = pair.lower().split(":")
    cls = "other"
    for c in rules["classes"]:
        if vendor in c["vendors"] and (c.get("device_from") is None or int(device, 16) >= int(c["device_from"], 16)):
            cls = c["id"]
            break
    have.add(cls)
for r in rules["rules"]:
    if all(c in have for c in r["all"]) and not any(c in have for c in r.get("none", [])):
        print(r["image"] or "")
        print(r["why"])
        print("hybrid" if r.get("hybrid") else "")
        break
' "$@"
}

result=""
if [ -n "$rules" ] && command -v python3 >/dev/null 2>&1; then
    result="$(printf '%s' "$rules" | decide "${ids[@]}" 2>/dev/null)" || result=""
fi

if [ -z "$result" ]; then
    # No rules (offline?) or no Python: the page can decide from the code.
    echo "Couldn't decide here. Your code for the download page:"
    echo
    echo "    ${code}"
    echo
    echo "Paste it at ${PAGE} to see which RedFoxOS suits this computer,"
    echo "or open this link, which shows the same:"
    echo "    ${link}"
    exit 0
fi

image="$(sed -n 1p <<< "$result")"
why="$(sed -n 2p <<< "$result")"
hybrid="$(sed -n 3p <<< "$result")"
case "$image" in
    redfox-os) title="RedFoxOS (Intel & AMD)" ;;
    redfox-os-nvidia) title="RedFoxOS NVIDIA" ;;
    redfox-os-nvidia-legacy) title="RedFoxOS NVIDIA Legacy" ;;
    *) title="" ;;
esac

if [ -n "$title" ]; then
    echo "This computer: ${title}"
    echo "  It has ${why}."
else
    echo "No single download suits this computer: it has ${why}."
    echo "  Pick the one for the graphics you want to use."
fi
if [ "$hybrid" = hybrid ]; then
    echo
    echo "Two graphics chips: this computer has built-in graphics next to its NVIDIA card,"
    echo "like most laptops with NVIDIA. The NVIDIA download drives the card with NVIDIA's"
    echo "driver, and the built-in graphics keep working. If the screen stays black when the"
    echo "USB stick starts, choose \"Start RedFoxOS (basic graphics)\" in its menu."
fi
echo
if [ -n "$title" ]; then
    echo "Download it here (the page opens with it picked):"
else
    echo "The downloads (the page opens with this computer's graphics checked):"
fi
echo "    ${link}"
echo
echo "Nothing about this computer has been sent anywhere. Code, if you'd rather paste it: ${code}"

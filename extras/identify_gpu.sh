#!/usr/bin/env bash
# RedFoxOS graphics check (Linux).
#
#   curl -sL https://raw.githubusercontent.com/snakeeyes021/redfox-os/main/extras/identify_gpu.sh | bash
#
# Lists this computer's graphics and says which RedFoxOS download to get,
# by the name on its card on the download page. It reads only each display
# device's PCI vendor and device id, downloads RedFoxOS's graphics rules
# (files/system/usr/share/redfox/gpu-rules.json, the same rules the download
# page and RedFox Hub's image picker use) and decides here: nothing about
# this computer is sent anywhere. identify_gpu.ps1 does the same on Windows,
# with the same output.
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

echo "RedFoxOS graphics check"
echo
if [ "${#ids[@]}" -eq 0 ]; then
    echo "No graphics found."
else
    echo "Graphics found:"
    for id in "${ids[@]}"; do
        name=""
        if [ -z "${RFX_DEVICES+set}" ] && command -v lspci >/dev/null 2>&1; then
            name="$(lspci -d "$id" 2>/dev/null | head -n1 | cut -d' ' -f2- | sed 's/^[^:]*: //')"
        fi
        if [ -n "$name" ]; then echo "  ${name} (${id})"; else echo "  ${id}"; fi
    done
fi
echo

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

# The decision, the same way the download page and Hub make it: each device
# gets the first class it matches, then the first rule whose classes all fit
# wins. Prints the image id, then the reason, then "hybrid" or nothing.
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
    if [ -n "$rules" ]; then
        echo "This check needs Python 3, which this computer doesn't have,"
    else
        echo "Couldn't download RedFoxOS's graphics rules (is this computer online?),"
    fi
    echo "so it can't say which download to get. Choose by your graphics at"
    echo "  ${PAGE}"
    echo
    echo "Nothing about this computer has been sent anywhere."
    exit 0
fi

image="$(sed -n 1p <<< "$result")"
why="$(sed -n 2p <<< "$result")"
hybrid="$(sed -n 3p <<< "$result")"
# The download's name, as on the download page and in RedFox Hub
case "$image" in
    redfox-os) download="RedFoxOS (AMD & Intel)" ;;
    redfox-os-nvidia) download="RedFoxOS NVIDIA" ;;
    redfox-os-nvidia-legacy) download="RedFoxOS NVIDIA Legacy" ;;
    *) download="" ;;
esac

# Prints text in lines of up to 76 characters, indented by two spaces. (The
# Windows version wraps the same way, so both print the same.)
wrap() {
    local line="" word
    set -f
    for word in $1; do
        if [ -z "$line" ]; then
            line="$word"
        elif [ $((${#line} + 1 + ${#word})) -le 76 ]; then
            line="$line $word"
        else
            echo "  $line"
            line="$word"
        fi
    done
    set +f
    [ -z "$line" ] || echo "  $line"
}

if [ -n "$download" ]; then
    echo "Why this download:"
    wrap "This computer has ${why}."
else
    echo "No single download works best on your machine:"
    wrap "It has ${why}. Choose the download for the graphics you want to use."
fi
if [ "$hybrid" = hybrid ]; then
    echo
    echo "Two graphics chips:"
    wrap "This computer has built-in graphics next to its NVIDIA card, like most laptops with NVIDIA. The NVIDIA download drives the card with NVIDIA's driver, and the built-in graphics keep working. If the screen stays black when the USB stick starts, choose \"Start RedFoxOS (basic graphics)\" in its menu."
fi
echo
if [ -n "$download" ]; then
    # The page marks the card this anchor names
    echo "The download page, with it marked:"
    echo "  ${PAGE}#${image}"
else
    echo "The downloads are at:"
    echo "  ${PAGE}"
fi
echo
echo "Nothing about this computer has been sent anywhere."
if [ -n "$download" ]; then
    # The result comes last, on its own line: bold and red in a terminal,
    # plain when the output goes to a file or another program, or NO_COLOR
    # is set.
    echo
    echo "The download to get:"
    if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-dumb}" != dumb ]; then
        printf '\033[1;31m%s\033[0m\n' "$download"
    else
        printf '%s\n' "$download"
    fi
fi

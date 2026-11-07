#!/usr/bin/env bash
# RedFoxOS graphics check (Linux).
#
#   curl -sL https://raw.githubusercontent.com/snakeeyes021/redfox-os/main/extras/identify_gpu.sh | bash
#
# Lists this computer's display devices and prints a short code to paste into
# the download page (https://redfoxlabs.tech/download/), which shows the
# RedFoxOS image that suits them. The code is just each display device's PCI
# vendor and device id, e.g. "RFX1 8086:46a6 10de:1c03"; nothing else is read
# and nothing is sent anywhere. The page decides with the same rules as RedFox
# Hub's "(Recommended)" (files/system/usr/share/redfox/gpu-rules.json).
# The Windows version is identify_gpu.ps1.
set -euo pipefail

ids=()
for dev in /sys/bus/pci/devices/*; do
    [ -r "$dev/class" ] || continue
    case "$(cat "$dev/class")" in 0x03*) ;; *) continue ;; esac # display controllers
    vendor="$(cat "$dev/vendor")"
    device="$(cat "$dev/device")"
    ids+=("${vendor#0x}:${device#0x}")
done

if [ "${#ids[@]}" -eq 0 ]; then
    echo "No graphics device found."
else
    echo "Graphics found:"
    for id in "${ids[@]}"; do
        name=""
        if command -v lspci >/dev/null 2>&1; then
            name="$(lspci -d "$id" 2>/dev/null | head -n1 | cut -d' ' -f2-)"
        fi
        echo "  ${id}${name:+  ${name}}"
    done
fi
echo
echo "Your code for the download page:"
echo
echo "    RFX1 ${ids[*]:-none}"
echo
echo "Paste it at https://redfoxlabs.tech/download/ to see which RedFoxOS suits this computer."

# -----------------------------------------------------------------------------
# RedFoxOS GPU Detection Script
#
# Purpose
# -------
# This script attempts to identify the system’s primary GPU and determine which
# RedFoxOS image should be installed:
#
#   - redfox-os                → Intel or AMD GPUs
#   - redfox-os-nvidia         → Modern NVIDIA GPUs (Volta/Turing/Ampere/Ada;
#                                 GTX 16xx, RTX 20xx and newer, RTX/“A”-series,
#                                 most post-Pascal Quadro/Tesla cards)
#   - redfox-os-nvidia-legacy  → Legacy NVIDIA GPUs (Pascal / GTX 10xx and older)
#
# Rationale
# ---------
# RedFoxOS exists primarily to provide legacy NVIDIA driver support for
# Pascal-era GPUs on a Bluefin/Bazzite DX–style stack. Modern NVIDIA GPUs should
# use the standard NVIDIA image, while Intel and AMD GPUs require no NVIDIA
# drivers at all.
#
# Detection Strategy
# ------------------
# 1. The script first attempts to detect GPUs via `lspci`, preferring NVIDIA GPUs
#    when multiple GPUs are present (e.g. hybrid Intel + NVIDIA systems).
#
# 2. If an NVIDIA GPU is detected and `nvidia-smi` is available and functional,
#    the script uses NVIDIA compute capability to classify the GPU:
#
#       - Compute capability ≤ 6.x → legacy (Maxwell/Pascal and older)
#       - Compute capability ≥ 7.x → modern (Volta and newer)
#
#    This is the most reliable method and correctly handles consumer, workstation,
#    and data-center GPUs (GTX/RTX, Quadro, Tesla, RTX A-series, etc.).
#
# 3. If `nvidia-smi` is unavailable or non-functional, the script falls back to
#    heuristic name matching based on the GPU’s PCI device string. This works
#    well for common consumer GPUs but may be less precise for older or unusually
#    named professional cards.
#
# Assumptions & Limitations
# -------------------------
# - This script assumes shell access to a Linux system with standard utilities
#   (`lspci`, optionally `nvidia-smi`).
# - In containers, virtual machines, or systems without PCI visibility, GPU
#   detection may be incomplete or misleading.
# - When NVIDIA GPUs cannot be conclusively identified as Pascal-era, the script
#   defaults to the modern NVIDIA image, as the legacy image exists specifically
#   to support Pascal and older hardware.
# - If no GPU can be detected, the script defaults to `redfox-os`.
#
# This script is intended as a convenience tool, not a replacement for manual
# hardware verification in edge cases.
# -----------------------------------------------------------------------------


#!/usr/bin/env bash
set -euo pipefail

# Prints one of:
#   redfox-os
#   redfox-os-nvidia
#   redfox-os-nvidia-legacy

have() { command -v "$1" >/dev/null 2>&1; }

# Return GPU controller lines (VGA/3D/Display)
gpu_lines() {
  if have lspci; then
    lspci -nn | grep -iE 'vga compatible controller|3d controller|display controller' || true
  else
    echo ""
  fi
}

# Prefer an NVIDIA GPU if present (common hybrid laptops / iGPU+dGPU)
pick_preferred() {
  local lines="$1"
  if echo "$lines" | grep -qi 'nvidia'; then
    echo "$lines" | grep -i 'nvidia' | head -n1
  else
    echo "$lines" | head -n1
  fi
}

# Classify NVIDIA using compute capability (best signal)
# Legacy iff compute capability major <= 6 (Pascal and older)
classify_nvidia_by_cc() {
  have nvidia-smi || return 1

  # Query compute capability; works if driver is installed + device exposed.
  local cc
  cc="$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader 2>/dev/null | head -n1 | tr -d '[:space:]')" || true
  [[ -n "${cc:-}" ]] || return 1

  local major
  major="$(echo "$cc" | awk -F. '{print $1+0}')"

  if [[ "$major" -le 6 ]]; then
    echo "redfox-os-nvidia-legacy"
  else
    echo "redfox-os-nvidia"
  fi
}

# Fallback heuristic based on lspci text when nvidia-smi isn't usable
# (Less perfect for pro/data-center naming; CC path above is strongly preferred.)
classify_nvidia_by_name() {
  local line_lc
  line_lc="$(echo "$1" | tr '[:upper:]' '[:lower:]')"

  # Explicit modern consumer patterns
  if echo "$line_lc" | grep -Eq 'rtx[[:space:]]*2[0-9]{2}|rtx[[:space:]]*3[0-9]{2}|rtx[[:space:]]*4[0-9]{2}|gtx[[:space:]]*16'; then
    echo "redfox-os-nvidia"
    return 0
  fi

  # Explicit legacy consumer patterns (and many older names)
  if echo "$line_lc" | grep -Eq 'gtx[[:space:]]*10|gtx[[:space:]]*9|gtx[[:space:]]*7|gtx[[:space:]]*6|quadro[[:space:]]*[kmp][0-9]|tesla[[:space:]]*[kmp][0-9]'; then
    echo "redfox-os-nvidia-legacy"
    return 0
  fi

  # If we can't tell from the name, default to modern (usually safer for non-Pascal pro cards)
  # The whole point of legacy is Pascal support; unknown NVIDIA is more likely "modern" than "needs 470xx".
  echo "redfox-os-nvidia"
}

main() {
  local lines preferred

  lines="$(gpu_lines)"
  if [[ -z "${lines:-}" ]]; then
    # Minimal system without pciutils: default to non-nvidia image
    echo "redfox-os"
    exit 0
  fi

  preferred="$(pick_preferred "$lines")"

  if echo "$preferred" | grep -qi 'nvidia'; then
    if out="$(classify_nvidia_by_cc)"; then
      echo "$out"
      exit 0
    fi
    echo "$(classify_nvidia_by_name "$preferred")"
    exit 0
  fi

  # Intel/AMD => base image
  if echo "$preferred" | grep -qiE 'intel|amd|advanced micro devices|ati'; then
    echo "redfox-os"
    exit 0
  fi

  # Unknown vendor => base image
  echo "redfox-os"
}

main "$@"

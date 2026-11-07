#!/usr/bin/env bash
# Swap Bazzite's kernel for Fedora's in the live system. Bazzite's kernel is
# signed with Universal Blue's key, which a new machine doesn't trust yet, so
# the live ISO couldn't boot with Secure Boot on. Fedora's kernel is signed for
# the shim on the ISO. The installed system keeps Bazzite's kernel; the
# installer queues Universal Blue's key for enrolment (anaconda.sh).
# Adapted from Bazzite's installer/titanoboa_hook_preinitramfs.sh (Apache-2.0).
set -exo pipefail

kernel_pkgs=(
    kernel
    kernel-core
    kernel-devel
    kernel-devel-matched
    kernel-modules
    kernel-modules-core
    kernel-modules-extra
)
dnf -y versionlock delete "${kernel_pkgs[@]}" || :
dnf --setopt=protect_running_kernel=False -y remove "${kernel_pkgs[@]}"
(cd /usr/lib/modules && rm -rf -- ./*)
# Bazzite excludes the kernel from Fedora's repos; clear that for this install.
dnf -y --repo fedora,updates --setopt='*.excludepkgs=' --setopt='excludepkgs=' \
    --setopt=tsflags=noscripts install kernel kernel-core kernel-modules
kernel=$(find /usr/lib/modules -maxdepth 1 -type d -printf '%P\n' | grep .)
depmod "$kernel"

# Firmware for NVIDIA cards, which the live system drives with nouveau.
dnf install -yq nvidia-gpu-firmware || :
dnf clean all -yq

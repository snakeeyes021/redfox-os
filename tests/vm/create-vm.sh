#!/usr/bin/env bash
# Create the RedFox test VM: an unattended install of Bazzite GNOME (the
# normal starting point for a rebase to RedFox), in the user's libvirt
# session (qemu:///session), the same place virt-manager's "QEMU/KVM User
# session" shows.
#
# Usage: tests/vm/create-vm.sh [path/to/Fedora-Silverblue-ostree-x86_64-*.iso]
#
# The Silverblue ISO is only used for its installer (Anaconda), which pulls
# the Bazzite image from ghcr.io via the kickstart's `ostreecontainer` line.
set -euo pipefail

NAME="${VM_NAME:-redfox-test}"
IMAGE="${VM_IMAGE:-ghcr.io/ublue-os/bazzite-gnome:stable}"
VM_USER="${VM_USER:-tester}"
VM_PASSWORD="${VM_PASSWORD:-redfox}"
SSH_PORT="${VM_SSH_PORT:-2223}"
MEMORY_MB="${VM_MEMORY_MB:-8192}"
VCPUS="${VM_VCPUS:-6}"
DISK_GB="${VM_DISK_GB:-80}"
KEY="${HOME}/.ssh/redfox-test"
ISO="${1:-$(ls -1 "${HOME}"/Downloads/Fedora-Silverblue-ostree-x86_64-*.iso 2>/dev/null | sort -V | tail -n1)}"
HERE="$(cd "$(dirname "$0")" && pwd)"
export LIBVIRT_DEFAULT_URI=qemu:///session

if [ -z "${ISO}" ] || [ ! -f "${ISO}" ]; then
    echo "No Silverblue ISO found. Pass its path as the first argument." >&2
    exit 1
fi
if virsh dominfo "${NAME}" >/dev/null 2>&1; then
    echo "A VM named ${NAME} already exists. Remove it first:" >&2
    echo "  virsh -c qemu:///session undefine --nvram --remove-all-storage ${NAME}" >&2
    exit 1
fi

[ -f "${KEY}" ] || ssh-keygen -t ed25519 -N '' -C "${NAME}" -f "${KEY}"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

# virt-install can't find the kernel in the ostree installer ISO on its own,
# so boot the installer's kernel and initrd directly with the ISO attached.
xorriso -osirrox on -indev "${ISO}" \
    -extract /images/pxeboot/vmlinuz "${WORK}/vmlinuz" \
    -extract /images/pxeboot/initrd.img "${WORK}/initrd.img" 2>/dev/null
LABEL="$(isoinfo -d -i "${ISO}" | sed -n 's/^Volume id: //p')"
sed -e "s|@IMAGE@|${IMAGE}|g" \
    -e "s|@USER@|${VM_USER}|g" \
    -e "s|@PASSWORD@|${VM_PASSWORD}|g" \
    -e "s|@SSHKEY@|$(cat "${KEY}.pub")|g" \
    "${HERE}/redfox-test.ks.in" > "${WORK}/ks.cfg"
# Anaconda reads ks.cfg on its own from a volume labelled OEMDRV. The VM
# keeps both CD drives afterwards, so this ISO lives next to its disk.
OEMDRV="${HOME}/.local/share/libvirt/images/${NAME}-oemdrv.iso"
xorriso -as mkisofs -quiet -V OEMDRV -o "${OEMDRV}" "${WORK}/ks.cfg"

virt-install \
    --name "${NAME}" \
    --osinfo silverblue-unknown \
    --memory "${MEMORY_MB}" \
    --vcpus "${VCPUS}" \
    --cpu host-passthrough \
    --boot uefi,firmware.feature0.name=secure-boot,firmware.feature0.enabled=no,firmware.feature1.name=enrolled-keys,firmware.feature1.enabled=no \
    --disk "size=${DISK_GB},format=qcow2,bus=virtio,discard=unmap" \
    --network "user,backend.type=passt,model=virtio,portForward0.proto=tcp,portForward0.address=127.0.0.1,portForward0.range0.start=${SSH_PORT},portForward0.range0.to=22" \
    --graphics spice \
    --video virtio \
    --channel spicevmc \
    --disk "path=${ISO},device=cdrom,readonly=on" \
    --disk "path=${OEMDRV},device=cdrom,readonly=on" \
    --install "kernel=${WORK}/vmlinuz,initrd=${WORK}/initrd.img,kernel_args=inst.stage2=hd:LABEL=${LABEL} inst.text console=tty0 console=ttyS0" \
    --serial "file,path=${HOME}/.local/share/libvirt/${NAME}-install.log" \
    --noautoconsole \
    --wait -1

cat <<MSG
Installed. The VM reboots into Bazzite and logs in as ${VM_USER} automatically.
  SSH:         ssh -i ${KEY} -p ${SSH_PORT} ${VM_USER}@127.0.0.1
  Screenshot:  virsh -c qemu:///session screenshot ${NAME} /tmp/${NAME}.png
  GUI:         virt-manager, connection "QEMU/KVM User session"
MSG

#!/usr/bin/bash
# Turns a RedFoxOS image into the live system of a live ISO (run by the
# Containerfile). Adapted from Bazzite's installer/build.sh (Apache-2.0),
# which follows https://github.com/ondrejbudai/bootc-isos.
set -exo pipefail

SRC=/src
LIVE_IMAGE=${LIVE_IMAGE:?}
INSTALL_IMAGE=${INSTALL_IMAGE:?}

# Create the directory that /root is symlinked to
mkdir -p "$(realpath /root)"
# podman (and dnf) need a /var/tmp, which the image build doesn't have
mkdir -p /var/tmp

# The image the installer puts on disk, stored in the live system so the
# install works offline. With the host's storage mounted (as in CI), copy it
# from there rather than pulling it again.
if mountpoint -q /usr/lib/containers/storage; then
    podman --storage-opt additionalimagestore=/usr/lib/containers/storage \
        save --format oci-archive "$INSTALL_IMAGE" | podman load
else
    podman pull "$INSTALL_IMAGE"
fi

cp -a "$SRC/system_files/." /

# A kernel that Secure Boot's shim trusts, and an initramfs that boots live.
"$SRC/kernel.sh"
dnf install -y dracut-live
kernel=$(kernel-install list --json pretty | jq -r '.[] | select(.has_kernel == true) | .version')
DRACUT_NO_XATTR=1 dracut -v --force --zstd --reproducible --no-hostonly \
    --add "dmsquash-live dmsquash-live-autooverlay" \
    "/usr/lib/modules/${kernel}/initramfs.img" "${kernel}"

dnf install -y livesys-scripts
sed -i "s/^livesys_session=.*/livesys_session=gnome/" /etc/sysconfig/livesys
systemctl enable livesys.service livesys-late.service

INSTALL_IMAGE="$INSTALL_IMAGE" "$SRC/anaconda.sh"

cp -af "$SRC/overrides/." /

# The ISO builder takes the EFI files (shim, grub) from /boot/efi.
dnf install -y grub2-efi-x64-cdboot
mkdir -p /boot/efi
cp -av /usr/lib/efi/*/*/EFI /boot/efi/
cp -v /boot/efi/EFI/fedora/grubx64.efi /boot/efi/EFI/BOOT/fbx64.efi

rm -f /etc/localtime
systemd-firstboot --timezone UTC

# The live root is an overlay in /run, which is small; ostree needs room in
# /var/tmp while installing.
rm -rf /var/tmp
mkdir /var/tmp
cat >/etc/systemd/system/var-tmp.mount <<'EOF'
[Unit]
Description=Larger tmpfs for /var/tmp on the live system

[Mount]
What=tmpfs
Where=/var/tmp
Type=tmpfs
Options=size=50%%,nr_inodes=1m,x-systemd.graceful-option=usrquota

[Install]
WantedBy=local-fs.target
EOF
systemctl enable var-tmp.mount

# Anaconda's systemd-tmpfiles --root=/mnt/sysroot fails while /mnt is a
# symlink (as on Fedora Atomic), so make it a directory (Aurora, 2026-11).
rm -rf /mnt
mkdir -p -m 0755 /mnt

mkdir -p /usr/lib/bootc-image-builder
cp "$SRC/iso.yaml" /usr/lib/bootc-image-builder/iso.yaml

dnf clean all

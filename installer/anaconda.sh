#!/usr/bin/env bash
# Anaconda, its kickstart, and the live session's tweaks. INSTALL_IMAGE is the
# image the installer puts on disk, e.g. ghcr.io/snakeeyes021/redfox-os:latest.
# Adapted from Bazzite's installer/titanoboa_hook_postrootfs.sh (Apache-2.0).
set -exo pipefail

INSTALL_IMAGE=${INSTALL_IMAGE:?}
SECUREBOOT_KEY=/usr/share/ublue-os/sb_pubkey.der
SECUREBOOT_DOC_URL=https://github.com/snakeeyes021/redfox-os#secure-boot
SECUREBOOT_DOC_URL_QR=/usr/share/ublue-os/secure_boot_qr.png

dnf -qy versionlock clear

# Anaconda's web interface, and Firefox to show it in
dnf install -qy --enable-repo=fedora-cisco-openh264 --allowerasing \
    firefox anaconda-live libblockdev-{btrfs,lvm,dm}
mkdir -p /var/lib/rpm-state # Needed for Anaconda Web UI
# Dialogs (yad) with a QR code for the Secure Boot instructions, and GParted
dnf install -qy --setopt=install_weak_deps=0 qrencode yad
dnf install -qy gparted

# Universal Blue's Secure Boot key, which signs Bazzite's kernel and modules.
mkdir -p /usr/share/ublue-os
if [ -f /etc/pki/akmods/certs/akmods-ublue.der ]; then
    cp /etc/pki/akmods/certs/akmods-ublue.der "$SECUREBOOT_KEY"
else
    curl --retry 3 -fLo "$SECUREBOOT_KEY" https://github.com/ublue-os/akmods/raw/main/certs/public_key.der
fi
qrencode -o "$SECUREBOOT_DOC_URL_QR" "$SECUREBOOT_DOC_URL"

cat >>/usr/share/anaconda/interactive-defaults.ks <<EOF

%pre
mkdir -p /tmp/anaconda_custom_logs
%end

# Must match efi_dir in the profile (profile.d/redfox.conf)
%pre-install --erroronfail
rm -rf /mnt/sysroot/boot/efi/EFI/fedora
%end

%onerror
run0 --user=liveuser yad --timeout=0 --text-info --no-buttons --width=600 --height=400 \
    --text="Something went wrong during the installation. Please report it at https://github.com/snakeeyes021/redfox-os/issues with this log." \
    < /tmp/anaconda.log
%end

ostreecontainer --url=$INSTALL_IMAGE --transport=containers-storage --no-signature-verification
%include /usr/share/anaconda/post-scripts/redfox-switch-to-registry.ks
%include /usr/share/anaconda/post-scripts/disable-fedora-flatpak.ks
%include /usr/share/anaconda/post-scripts/restore-selinux-labels.ks
%include /usr/share/anaconda/post-scripts/secureboot-enroll-key.ks
%include /usr/share/anaconda/post-scripts/secureboot-docs.ks
EOF

# The image was installed from the ISO; point the system at the signed image
# in the registry, so updates come from there and are checked against
# RedFoxOS's signing key (the image's /etc/containers/policy.json).
cat >/usr/share/anaconda/post-scripts/redfox-switch-to-registry.ks <<EOF
%post --erroronfail --log=/tmp/anaconda_custom_logs/bootc-switch.log
bootc switch --mutate-in-place --enforce-container-sigpolicy --transport registry $INSTALL_IMAGE
%end
EOF

# Queue Universal Blue's key for enrolment: at the next boot the firmware's
# MOK manager asks for the password "universalblue".
cat >/usr/share/anaconda/post-scripts/secureboot-enroll-key.ks <<EOF
%post --erroronfail --nochroot --log=/tmp/anaconda_custom_logs/secureboot-enroll-key.log
set -oue pipefail

readonly ENROLLMENT_PASSWORD="universalblue"
readonly SECUREBOOT_KEY="$SECUREBOOT_KEY"

if [[ ! -d "/sys/firmware/efi" ]]; then
    echo "EFI mode not detected. Skipping key enrollment."
    exit 0
fi
if [[ ! -f "\$SECUREBOOT_KEY" ]]; then
    echo "Secure boot key not provided: \$SECUREBOOT_KEY"
    exit 0
fi

mokutil --timeout -1 || :
echo -e "\$ENROLLMENT_PASSWORD\n\$ENROLLMENT_PASSWORD" | mokutil --import "\$SECUREBOOT_KEY" || :
%end
EOF

cat >/usr/share/anaconda/post-scripts/secureboot-docs.ks <<EOF
%post --nochroot --log=/tmp/anaconda_custom_logs/secureboot-docs.log
LC_ALL=C mokutil -t "$SECUREBOOT_KEY" | grep -q "is already in the enrollment request" && \
    run0 --user=liveuser yad --timeout=0 --on-top --button=OK:0 --image="$SECUREBOOT_DOC_URL_QR" \
    --text="<b>One more step at the next start</b>\n\nA blue <b>MOK management</b> screen will appear.\nChoose <b>Enroll MOK</b>, then <b>Continue</b>, then <b>Yes</b>,\ntype the password <b>universalblue</b> and choose <b>Reboot</b>.\n\nThis lets Secure Boot start RedFoxOS. Instructions:\n$SECUREBOOT_DOC_URL"
%end
EOF

### The live session ###

# Nothing that sets up, updates or fills in a system: the live session is only
# for trying RedFoxOS and installing it. (The installed system runs them all;
# its Flatpaks are installed at first boot.)
(
    set +e
    for s in \
        rpm-ostree-countme.service \
        rpm-ostreed-automatic.timer \
        uupd.timer \
        bootloader-update.service \
        tailscaled.service \
        bazzite-hardware-setup.service \
        bazzite-flatpak-manager.service \
        bazzite-iwd-migration.service \
        ublue-hardware-setup.service \
        ublue-system-setup.service \
        ublue-guest-user.service \
        ublue-os-media-automount.service \
        ublue-nvidia-flatpak-runtime-sync.service \
        ublue-nvidia-flatpak-runtime-verify.service \
        system-flatpak-setup.timer \
        flatpak-add-fedora-repos.service \
        redfox-flatpak-fonts.service \
        redfox-greenboot-stale-check.service \
        greenboot-set-rollback-trigger.service \
        greenboot-healthcheck.service \
        brew-setup.service \
        brew-update.timer \
        brew-upgrade.timer \
        input-remapper.service \
        check-sb-key.service; do
        if systemctl list-unit-files "$s" >/dev/null 2>&1; then systemctl disable "$s"; fi
    done
    for s in \
        podman-auto-update.timer \
        user-flatpak-setup.timer \
        bazzite-user-setup.service \
        bazzite-dynamic-fixes.service \
        redfox-user-setup.service \
        ublue-user-setup.service; do
        if systemctl --global list-unit-files "$s" >/dev/null 2>&1; then systemctl --global disable "$s"; fi
    done
)

# No Steam or Bazzite Portal at login, and no Fedora welcome screen
rm -vf /etc/skel/.config/autostart/steam*.desktop /etc/skel/.config/autostart/bazzite-portal.desktop
rm -vf /etc/xdg/autostart/bazzite-announcement.desktop /etc/xdg/autostart/tech.redfoxlabs.Hub.welcome.desktop
sed -i 's@\[Desktop Entry\]@\[Desktop Entry\]\nHidden=true@g' \
    /usr/share/anaconda/gnome/org.fedoraproject.welcome-screen.desktop || :
rm -vf /etc/profile.d/verify_motd.sh
rm -f /usr/bin/rpm-ostree # never to be run on the live system

glib-compile-schemas /usr/share/glib-2.0/schemas

# The fox in Anaconda's web interface (with branding.css from overrides/)
mkdir -p /usr/share/cockpit/branding/fedora
cp /usr/share/icons/hicolor/256x256/apps/redfox-logo.png /usr/share/cockpit/branding/fedora/logo.png

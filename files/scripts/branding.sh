#!/usr/bin/env bash
# Make the image report itself as RedFoxOS wherever a person sees it.
#
# os-release says what this is: ID=redfox, built on Bazzite and Fedora
# (ID_LIKE="bazzite fedora"). Tools that know only Fedora or Bazzite find
# them through ID_LIKE. The identifiers Bazzite's and Universal Blue's
# tooling reads stay as they are: VARIANT_ID, VERSION*, CPE_NAME, and
# image-info.json's base-image-name, fedora-version, image-tag and
# image-branch. See docs/branding.md for what reads what.
#
# Runs last, after every other module has installed its files.
set -euo pipefail

OS_RELEASE=/usr/lib/os-release
IMAGE_INFO=/usr/share/ublue-os/image-info.json
REGISTRY=ghcr.io/snakeeyes021
# BlueBuild passes the recipe's image name (redfox-os, redfox-os-nvidia, ...).
IMAGE_NAME="${IMAGE_NAME:-redfox-os}"

set_os_release() {
    local key="$1" value="$2"
    if grep -q "^${key}=" "$OS_RELEASE"; then
        sed -i "s|^${key}=.*|${key}=\"${value}\"|" "$OS_RELEASE"
    else
        echo "${key}=\"${value}\"" >> "$OS_RELEASE"
    fi
}

# --- os-release: the identity ---
# Plain, unquoted values, as Fedora writes them: some scripts read ID with
# grep and cut and don't strip quotes.
sed -i 's|^ID=.*|ID=redfox|' "$OS_RELEASE"
set_os_release ID_LIKE "bazzite fedora"

# --- os-release: the names people see ---
# Bazzite's BUILD_ID looks like "Stable (F44.20261026)"; keep the version part.
FEDORA_BUILD="$(sed -n 's/^BUILD_ID=.*(\(.*\)).*/\1/p' "$OS_RELEASE")"
BASE_VERSION="$(sed -n 's/^OSTREE_VERSION=.\([^"'\'']*\).*/\1/p' "$OS_RELEASE")"
set_os_release NAME "RedFoxOS"
set_os_release PRETTY_NAME "RedFoxOS"
set_os_release LOGO "redfox-logo"
set_os_release ANSI_COLOR "0;38;2;178;34;52"
set_os_release DEFAULT_HOSTNAME "redfox"
set_os_release HOME_URL "https://redfoxlabs.tech"
set_os_release DOCUMENTATION_URL "https://github.com/snakeeyes021/redfox-os#readme"
set_os_release SUPPORT_URL "https://github.com/snakeeyes021/redfox-os/issues"
set_os_release BUG_REPORT_URL "https://github.com/snakeeyes021/redfox-os/issues"
set_os_release BOOTLOADER_NAME "RedFoxOS${FEDORA_BUILD:+ ($FEDORA_BUILD)}"
set_os_release IMAGE_ID "${IMAGE_NAME}${BASE_VERSION:+-${BASE_VERSION%.*}}"
echo "os-release:"
cat "$OS_RELEASE"

# --- image-info.json: which image this is ---
# Bazzite's scripts read image-name (they check it for "nvidia", "deck" and
# "dx", which our names keep or lack the same way) and show image-ref.
if [ -f "$IMAGE_INFO" ]; then
    tmp="$(mktemp)"
    jq --arg name "$IMAGE_NAME" --arg ref "ostree-image-signed:docker://${REGISTRY}/${IMAGE_NAME}" \
        '."image-name" = $name | ."image-vendor" = "snakeeyes021" | ."image-ref" = $ref' \
        "$IMAGE_INFO" > "$tmp"
    install -m 0644 "$tmp" "$IMAGE_INFO"
    rm -f "$tmp"
    echo "image-info.json:"
    cat "$IMAGE_INFO"
fi

# --- Terminal banner: Bazzite's tips (gaming, and links to Bazzite's docs);
# RedFox ships its own in tips/20-redfox.md ---
rm -f /usr/share/ublue-os/motd/tips/10-ublue.md /usr/share/ublue-os/motd/tips/20-bazzite.md \
      /usr/share/ublue-os/motd/tips/sv/10-ublue.md /usr/share/ublue-os/motd/tips/sv/20-bazzite.md
# Swedish locales get Bazzite's own banner (its name and its issue, docs,
# Discord and Bluesky links). RedFox has no Swedish one, so they get ours.
if [ -f /usr/share/ublue-os/motd/template.sv.md ]; then
    ln -sf template.md /usr/share/ublue-os/motd/template.sv.md
fi

# --- Icons: pick up redfox-logo ---
gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true

# --- Boot splash: the initramfs carries its own copy of the Plymouth theme,
# built into the Bazzite base image, so it still showed Bazzite's watermark.
# Rebuild it with the same dracut configuration so it picks up ours. ---
KVER="$(ls -1 /usr/lib/modules | sort -V | tail -n1)"
echo "Rebuilding the initramfs for ${KVER}..."
dracut --force --kver "$KVER" --reproducible --add ostree \
    "/usr/lib/modules/${KVER}/initramfs.img"
chmod 0600 "/usr/lib/modules/${KVER}/initramfs.img"

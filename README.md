# RedFoxOS

![Platform](https://img.shields.io/badge/Platform-BlueBuild%20%2F%20bootc-blue) ![Packaging](https://img.shields.io/badge/Packaging-OCI%20image-orange) ![License](https://img.shields.io/badge/License-Apache%202.0-blue) ![Release](https://img.shields.io/github/v/release/snakeeyes021/redfox-os?label=Release)

## Purpose
The purpose of RedFoxOS is to round out the offerings of Bazzite, both with some of the features included in Bluefin DX (and therefore Bazzite DX) as well as a few features, apps, and configs not present in either.

Its primary raison d'être is to provide driver support for Pascal-series Nvidia cards on a Bluefin/Bazzite DX-style OS. While vanilla Bazzite will support Pascal cards through 2028ish, both Bluefin (vanilla or DX) and Bazzite DX have dropped support; therefore the only way to achieve said developer experience with Pascal cards is to configure it oneself on top of vanilla Bazzite. Enter RedFoxOS.

## Features

### Core Developer Experience
- [x] **Containerization:** Docker (Engine & CLI), Podman (with Compose & TUI), Incus, LXC
- [x] **Virtualization:** Libvirt/QEMU, Cockpit (Machines, Podman, Bridge), System-level GNOME Boxes + Virt-Manager
- [x] **Development:** VS Code (system install), Android Tools, BPF Tools (bpftop, bpftrace), Sysprof, pixi/uv
- [x] **CLI Utilities:** zsh, restic, rclone, ccache
- [x] **Editor:** Zed (ujust recipe installer)
- [ ] **AI Utilities:** Cursor (system), Antigravity (system), Antigravity IDE (system), ramalama (system), Ollama (system), OpenClaw (ujust)

### Desktop & Media
- [x] **NVIDIA Pascal Support:** Built on `bazzite-gnome-nvidia` for legacy driver support
- [x] **Curated App Packs:** Creative, Productivity, Dev, and several other curated app bundle installers, all installable via simple ujust recipes
- [ ] **GNOME config:** Several preset desktop environment configs, including a mostly "vanilla" GNOME config, all available via simple ujust recipes
- [ ] **More:** Wallpaper, keyboard shortcuts, shell prompt, etc.

## Installation

> [!CAUTION]
> **GNOME ONLY:** This image is based on GNOME. **Do not rebase** from a KDE-based image (like Kinoite or mainline Bazzite), as this can cause significant desktop environment conflicts. If you are currently on KDE, please install a fresh copy of a GNOME-based Fedora Atomic distro first, then rebase to RedFoxOS.

We have three images available, depending on your hardware:

*   **`redfox-os`**: For Intel and AMD GPUs.
*   **`redfox-os-nvidia`**: For modern Nvidia GPUs (GTX 16xx, RTX 20xx and newer).
*   **`redfox-os-nvidia-legacy`**: For legacy Nvidia GPUs (Pascal/GTX 10xx series and older).

> [!TIP]
> **Not sure which one to pick?**
>
> Run this command in your terminal to automatically detect your GPU and see which image is right for you:
>
> ```bash
> curl -sL https://raw.githubusercontent.com/snakeeyes021/redfox-os/main/extras/identify_gpu.sh | bash
> ```

### Rebasing from Bluefin or Bazzite (GNOME)
To switch to RedFoxOS from an existing GNOME-based Universal Blue installation, choose the command that corresponds to your hardware:

**1. Rebase to the signed image**

*   **Intel/AMD:**
    ```bash
    rpm-ostree rebase ostree-image-signed:docker://ghcr.io/snakeeyes021/redfox-os:latest
    ```

*   **Nvidia (Modern):**
    ```bash
    rpm-ostree rebase ostree-image-signed:docker://ghcr.io/snakeeyes021/redfox-os-nvidia:latest
    ```

*   **Nvidia (Legacy):**
    ```bash
    rpm-ostree rebase ostree-image-signed:docker://ghcr.io/snakeeyes021/redfox-os-nvidia-legacy:latest
    ```

**2. Reboot**
```bash
systemctl reboot
```

> [!NOTE]
> **Fedora Silverblue Users:** Direct rebasing from Fedora Silverblue is not officially supported. Silverblue's default configuration will reject the signed commands above. While we recommend switching from a fresh Bluefin or Bazzite (GNOME) install first, advanced users can perform a direct migration by using a "two-step" method:
>
> 1.  **Rebase to unverified:** Modify the appropriate command above to use `ostree-unverified-registry` (instead of `ostree-image-signed`). This installs the OS but temporarily bypasses the initial verification check.
> 2.  **Reboot:** Restart your system to boot into RedFoxOS.
> 3.  **Rebase to signed:** Once rebooted, run the original signed command listed above. This ensures your system is properly verified for all future updates.

## Rolling Back and Switching Builds

Every update keeps the previous system. To go back to it, pick it in the boot menu, or run:

```bash
ujust rollback-helper            # a menu
ujust rollback-helper rollback   # boot the previous system next time
ujust rollback-helper list       # recent builds of your channel (latest or unstable)
ujust rollback-helper rebase 20261101   # a dated stable build; also: a commit, latest, unstable
```

A dated or commit build doesn't update by itself; `ujust rollback-helper rebase latest` (or `unstable`) follows updates again.

## Verification

These images are signed with [Sigstore](https://www.sigstore.dev/)'s [cosign](https://github.com/sigstore/cosign). You can verify the signature by downloading the `cosign.pub` file from this repo and running:

```bash
cosign verify --key cosign.pub ghcr.io/snakeeyes021/redfox-os
```

## ISO Installation

Each image has a live ISO: it starts a RedFoxOS desktop from a USB stick, where you can try it and then install it. Download the ISO for your graphics from **https://redfoxlabs.tech/download**. Not sure which one? The page can tell you.

1. Write the ISO to a USB stick of 16 GB or more, with [Fedora Media Writer](https://flathub.org/apps/org.fedoraproject.MediaWriter), balenaEtcher or `dd`.
2. Start the computer from the stick. It needs UEFI (not legacy/CSM mode).
3. Choose **Install RedFoxOS**, pick the disk, and create your account.
4. Restart. If Secure Boot is on, enrol the key once (below).
5. Your apps install in the background at the first start, once you're online.

The ISOs install the stable images. For `unstable`, install stable first, then run `ujust rollback-helper rebase unstable`.

To check a download: `sha256sum -c redfox-os.iso-CHECKSUM`, or with this repo's key, `cosign verify-blob --key cosign.pub --signature redfox-os.iso.sig redfox-os.iso`. See [docs/iso.md](docs/iso.md) for how the ISOs are made.

## Secure Boot

RedFoxOS uses Bazzite's kernel, which is signed with Universal Blue's key. The installer queues that key for enrolment. At the first restart after installing, a blue **MOK management** screen appears:

1. Choose **Enroll MOK**, then **Continue**, then **Yes**.
2. Type the password `universalblue`.
3. Choose **Reboot**.

If you missed the screen, or rebased from another image, run `ujust enroll-secure-boot-key` and restart.

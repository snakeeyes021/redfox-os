# SamsoniteOS

### Purpose
The purpose of SamsoniteOS is to round out the offerings of Bazzite, both with some of the features included in Bluefin DX (and therefore Bazzite DX) as well as a few features, apps, and configs not present in either. Its primary raison d'être is to provide driver support for Pascal-series Nvidia cards on a Bluefin/Bazzite DX-style OS. While vanilla Bazzite will support Pascal cards through 2028ish, both Bluefin, vanilla or DX, and Bazzite DX, have dropped support; therefore the only way to achieve said developer experience with Pascal cards is to configure it oneself on top of vanilla Bazzite. Enter SamsoniteOS.

### Feature Status

**Core Developer Experience**
- [x] **Containerization:** Docker (Engine & CLI), Podman (with Compose & TUI), Incus, LXC
- [x] **Virtualization:** Libvirt/QEMU, Cockpit (Machines, Podman, Bridge)
- [x] **Development:** VS Code (System install), Android Tools, BPF Tools (bpftop, bpftrace), Sysprof
- [x] **CLI Utilities:** zsh, restic, rclone, ccache, ramalama (Local AI)
- [ ] **Editor:** Zed (System install)
- [ ] **Additional AI Utilities:** Cursor, Gemini CLI
- [ ] **Unified Virtualization:** System-level GNOME Boxes + Virt-Manager integration.

**Desktop & Media**
- [x] **NVIDIA Pascal Support:** Built on `bazzite-gnome-nvidia` for legacy driver support.
- [x] **Creative Suite:** Blender, GIMP, Kdenlive, OBS Studio (Pre-installed Flatpaks).
- [ ] **Audio Production:** A curated collection of music/audio tools.
- [ ] **Shell Customization:** Starship prompt integration.
- [ ] **GNOME Tweaks:** Further "vanilla" GNOME configuration.
- [ ] **More:** Wallpaper, keyboard shortcuts, etc.

### Installation

> [!CAUTION]
> **GNOME ONLY:** This image is based on GNOME. **Do not rebase** from a KDE-based image (like Kinoite or mainline Bazzite), as this can cause significant desktop environment conflicts. If you are currently on KDE, please install fresh using an ISO.  

*Multiple image channels coming soon:*
- ***Nvidia Closed*** *(pinned to driver version 580 for legacy card support)*
- ***Nvidia Open*** *(Nvidia GTX 16xx, RTX 20xx and above)*
- ***Intel/AMD*** *(all others)*  

**Rebasing from Silverblue, Bluefin, or Bazzite (GNOME):**

To switch to SamsoniteOS from an existing GNOME-based Fedora Atomic installation:

1.  **Rebase to the signed image:**
    ```bash
    rpm-ostree rebase ostree-image-signed:docker://ghcr.io/snakeeyes021/samsonite-os:latest
    ```

2.  **Reboot:**
    ```bash
    systemctl reboot
    ```

**ISO Installation:**

*ISO downloads coming soon.*

### Verification

These images are signed with [Sigstore](https://www.sigstore.dev/)'s [cosign](https://github.com/sigstore/cosign). You can verify the signature by downloading the `cosign.pub` file from this repo and running:

```bash
cosign verify --key cosign.pub ghcr.io/snakeeyes021/samsonite-os
```

# RedFoxOS

### Purpose
The purpose of RedFoxOS is to round out the offerings of Bazzite, both with some of the features included in Bluefin DX (and therefore Bazzite DX) as well as a few features, apps, and configs not present in either. Its primary raison d'être is to provide driver support for Pascal-series Nvidia cards on a Bluefin/Bazzite DX-style OS. While vanilla Bazzite will support Pascal cards through 2028ish, both Bluefin, vanilla or DX, and Bazzite DX, have dropped support; therefore the only way to achieve said developer experience with Pascal cards is to configure it oneself on top of vanilla Bazzite. Enter RedFoxOS.

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
> **GNOME ONLY:** This image is based on GNOME. **Do not rebase** from a KDE-based image (like Kinoite or mainline Bazzite), as this can cause significant desktop environment conflicts. If you are currently on KDE, please install a fresh copy of a GNOME-based Fedora Atomic distro first, then rebase to RedFoxOS.  

We have three images available, depending on your hardware:

- **`redfox-os`**: For Intel and AMD GPUs.
- **`redfox-os-nvidia`**: For modern Nvidia GPUs (GTX 16xx, RTX 20xx and newer).
- **`redfox-os-nvidia-legacy`**: For legacy Nvidia GPUs (Pascal/GTX 10xx series and older).

**Rebasing from Bluefin or Bazzite (GNOME):**

To switch to RedFoxOS from an existing GNOME-based Universal Blue installation, choose the command that corresponds to your hardware:

1.  **Rebase to the signed image:**

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

2.  **Reboot:**
    ```bash
    systemctl reboot
    ```

> [!NOTE]
> **Fedora Silverblue Users:** While it is certainly possible to rebase from Fedora Silverblue, we do not recommend it for casual users. Silverblue's default policy does not support our signed images out of the box, meaning the commands above will fail without additional system configuration that is outside the scope of this guide.

### Verification

These images are signed with [Sigstore](https://www.sigstore.dev/)'s [cosign](https://github.com/sigstore/cosign). You can verify the signature by downloading the `cosign.pub` file from this repo and running:

```bash
cosign verify --key cosign.pub ghcr.io/snakeeyes021/redfox-os
```

## ISO Installation

Generating ISOs turns out to be the trickiest part of maintaining a custom OS image like this, both in terms of the pipeline (Bazzite, and thus RedFoxOS, is built on bleeding-edge Fedora Rawhide; if Fedora pushes a change to, e.g., grub that flumoxes the build system that smooshes Anaconda and our image together into an ISO, then the ISO build pipeline breaks and there's not much we can do about it except wait) and logistics (publication, storage, costs, etc). At the time of this writing, just such a change in Fedora seems to be breaking the pipeline, best we can tell.

For this reason, we do not currently have ISOs available for download, and even if/when we are able to begin generating them again, we cannot guarantee consistent availability. We highly recommend users install via a rebase (using one of the three commands above) from a GNOME-based Universal Blue distribution. To do so, simply: 
1. Download an ISO for Bluefin or Bazzite (we recommend Bazzite; make sure to select a version with the GNOME desktop). 
2. Install as you normally would. 
3. Immediately run one of the above commands to rebase to your preferred version of RedFoxOS. 
4. Reboot. 
5. Profit.
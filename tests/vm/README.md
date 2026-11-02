# RedFox test VM

A Bazzite GNOME VM for trying RedFox changes before they reach `unstable`. It lives in the user's libvirt session (`qemu:///session`, "QEMU/KVM User session" in virt-manager), is called `redfox-test`, and logs in automatically as `tester` (password `redfox`, passwordless sudo).

## Create it

```bash
tests/vm/create-vm.sh ~/Downloads/Fedora-Silverblue-ostree-x86_64-44-1.7.iso
```

This is unattended and takes about 20 minutes, most of it downloading Bazzite. The Silverblue ISO only supplies the installer. The kickstart (`redfox-test.ks.in`) installs `ghcr.io/ublue-os/bazzite-gnome:stable`, the usual starting point for a rebase to RedFox. It also sets up SSH on `127.0.0.1:2223` with the key `~/.ssh/redfox-test`, which the script creates.

The VM boots without Secure Boot. Bazzite's kernel is signed with Universal Blue's key, which a fresh VM doesn't trust.

For a fresh start later, keep a copy of the disk while the VM is shut off:

```bash
qemu-img convert -O qcow2 ~/.local/share/libvirt/images/redfox-test.qcow2 \
    ~/.local/share/libvirt/images/redfox-test-bazzite-baseline.qcow2
```

To restore, shut the VM off and copy the baseline back over `redfox-test.qcow2`.

## Drive it

`tests/vm/vm` wraps the usual steps:

| Command | What it does |
| --- | --- |
| `vm ssh [cmd]` | Run a command in the VM. |
| `vm user [cmd]` | Run a command inside the desktop session (`gsettings`, `gnome-extensions`, `redfox-layout`, …). |
| `vm shot [file]` | Screenshot the VM's screen (default `/tmp/redfox-test.png`). |
| `vm push` | Copy this checkout's `files/system/usr` (plus `~/dev/smooth-overview`, and any extensions.gnome.org extensions from the recipe the VM lacks) into the VM's `/usr`, then reboot. |
| `vm restart-session` | Reboot. GDM only logs in automatically once per boot, so this is how to restart GNOME Shell. |
| `vm serve-image [tag]` | Push a locally built image to a registry on this machine (`127.0.0.1:5000`). |
| `vm rebase-local` | Rebase the VM onto that image and reboot. |

## Testing a feature branch

Images only build in CI for `unstable` and `main`, so a branch can be tested in three ways. Use the cheapest that covers the change.

1. **Quick loop: `vm push`.** For shell extensions, scripts in `/usr/bin`, ujust recipes, schemas and the RedFox dconf defaults. It unlocks the VM's `/usr` as a hotfix overlay (`ostree admin unlock --hotfix`), copies the files in and reboots, which takes about a minute. The overlay lasts until the next rebase or update. It does not run the recipe's dnf/flatpak/script modules, so it can't test package changes.

2. **Full image, built here.** For recipe changes (packages, modules, build scripts), and as the last check before merging into `unstable`:

   ```bash
   bluebuild build recipes/recipe-main.yml   # ~35 min; uses Docker if present
   tests/vm/vm serve-image localhost/redfox-os:latest
   tests/vm/vm rebase-local                  # ~3 min, then reboots
   ```

   That is the same path users take: a rebase from Bazzite onto the RedFox image. It runs unsigned (`ostree-unverified-registry`), which is fine for a test VM.

3. **Image built by CI.** Opening a pull request from the branch into `unstable` makes `bluebuild-unstable` build all three images and push them as `ghcr.io/snakeeyes021/redfox-os:pr-<number>-<fedora>`, e.g. `pr-26-44`. A VM (or a spare machine) can rebase onto that directly:

   ```bash
   sudo rpm-ostree rebase ostree-unverified-registry:ghcr.io/snakeeyes021/redfox-os:pr-26-44
   ```

   It's slower to iterate on than a local build, but it also covers the two NVIDIA images.

Before a branch is merged into `unstable`, it has had at least option 2 or 3 in the VM.

## Rebasing from other images

`create-vm.sh` takes `VM_NAME`, `VM_IMAGE`, `VM_SSH_PORT`, `VM_MEMORY_MB` and `VM_VCPUS`, so a VM can start from another uBlue image. `tests/vm/vm` reads `VM_NAME` and `VM_SSH_PORT` too:

```bash
VM_NAME=redfox-bluefin VM_IMAGE=ghcr.io/ublue-os/bluefin:stable VM_SSH_PORT=2224 VM_MEMORY_MB=6144 \
    tests/vm/create-vm.sh
VM_NAME=redfox-bluefin VM_SSH_PORT=2224 tests/vm/vm rebase-local
```

### Bluefin → RedFox (tested 2026-11-01)

Bluefin stable (F44, GNOME 50.6), rebased onto a local build of `feat/layout-modes`:

- **The rebase works**, and RedFox boots and logs in normally. It takes much longer than from Bazzite: the two share no layers, so the whole image (about 9 GB) is fetched. That was about 45 minutes in the VM, against 3 minutes from Bazzite. `vm rebase-local` runs the rebase as a detached unit for this reason. Over plain SSH, the rpm-ostree client stalled when the connection dropped.
- **Some packages go down a version** when Bluefin's build is newer than RedFox's Bazzite base (Tailscale, util-linux, WebKitGTK, …). They come back with the next RedFox update; a rollback returns to Bluefin as it was.
- **Docker didn't start:** `docker.socket` failed with "Failed to resolve group 'docker'". This isn't Bluefin-specific; it's the same for any rebase, from Bazzite too. Fixed on `fix/docker-group-after-rebase`.
- **Extensions:** RedFox's default extension list replaces Bluefin's, unless the user had changed theirs. Bluefin's dock and its Logo Menu go away until a layout turns a dock on (`ujust preset-dock-ubuntu` and so on). Search Light and Gradia's integration aren't in RedFox at all, so anyone who had them enabled loses them without a message.
- **Flatpaks:** apps from Flathub stay. Apps from Fedora's own Flatpak remote are removed by BlueBuild's default-flatpaks module, which then installs RedFox's default apps from Flathub. (This test VM had Fedora-remote apps only because it was installed from the Silverblue ISO; a Bluefin ISO install uses Flathub.)
- **Settings:** the dconf profile becomes RedFox's (`redfox` first), and Bluefin's `distro` defaults are replaced by Bazzite's, so no Bluefin defaults leak through.
- **Left over in `/etc`** (all harmless): tuned's active profile, the installer's firewalld zone, CUPS state.
- `os-release` still says Bazzite. That's the branding work, not the rebase.

The disks are kept: `redfox-bluefin.qcow2` (rebased) and `redfox-bluefin-baseline.qcow2` (Bluefin before the rebase).

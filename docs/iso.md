# RedFoxOS live ISOs

Each of the three stable images has a live ISO. It boots into a RedFoxOS desktop, where you can try the system and then install it. Unstable users install a stable ISO, then rebase (`ujust rollback-helper rebase unstable`).

| ISO | Installs |
|---|---|
| `redfox-os.iso` | `ghcr.io/snakeeyes021/redfox-os:latest` (Intel and AMD graphics) |
| `redfox-os-nvidia.iso` | `ghcr.io/snakeeyes021/redfox-os-nvidia:latest` (GTX 16xx, RTX 20xx and newer) |
| `redfox-os-nvidia-legacy.iso` | `ghcr.io/snakeeyes021/redfox-os-nvidia-legacy:latest` (GTX 10xx and older) |

Each ISO has a `.iso-CHECKSUM` file (SHA-256) and a `.iso.sig` file, signed with the same key as the images:

```bash
sha256sum -c redfox-os.iso-CHECKSUM
cosign verify-blob --key cosign.pub --signature redfox-os.iso.sig redfox-os.iso
```

## What happens on the ISO

- **The live session** is the Intel/AMD image on Fedora's own kernel, in all three ISOs. Fedora's kernel is signed for the shim, so the ISO starts with Secure Boot on. Bazzite's kernel is signed with Universal Blue's key, which a new machine doesn't trust yet. NVIDIA cards run on nouveau in the live session.
- **A welcome dialog** offers *Install RedFoxOS* or *Try It First*. The installer is also first in the dash. It warns about less than 8 GB of memory, and switches off machines started in legacy (CSM) mode, since the ISO is UEFI-only.
- Nothing that sets up or updates a system runs in the live session: no update timers, Flatpak installs, Steam or Bazzite Portal.

## What the installer does

The installer is Anaconda's web interface.
- The user picks the disk, the language and the keyboard, and **creates their account**. RedFoxOS, like Bazzite GNOME, has no GNOME Initial Setup, so the installer is where the account is made. The root account section is hidden.
- The default layout is btrfs with zstd compression, as on Bazzite.
- **The image comes from the ISO**, so the install works offline. Afterwards `bootc switch --enforce-container-sigpolicy` points the system at the signed image on ghcr.io (`ostree-image-signed:docker://ghcr.io/snakeeyes021/<image>:latest`). Updates come from there and are checked against RedFoxOS's key. The first update may download the whole image once, because the copy on the ISO was stored in a different format.
- **Secure Boot:** the installer queues Universal Blue's key (`/usr/share/ublue-os/sb_pubkey.der`) with `mokutil`, and shows how to finish. At the next start the blue MOK screen appears: *Enroll MOK* → *Continue* → *Yes*, password `universalblue`, *Reboot*. Without that, Secure Boot refuses Bazzite's kernel. See the README's Secure Boot section.
- **Flatpaks** install at the first boot, once there's a network, the same as after a rebase (Bazzite's Flatpak manager and the image's `system-flatpak-setup`). They aren't on the ISO, which keeps it a few GB smaller.

## How it's built

`.github/workflows/build-live-iso.yml`, run by hand: *Actions › Build live ISOs › Run workflow*. Pick the tag (`latest`), one ISO or all three, and whether to publish.

1. Frees the runner's disk, and puts podman's storage on a compressed btrfs file.
2. Pulls the images, accepting only ones signed with `cosign.pub`.
3. Builds the live system from `installer/Containerfile`. `installer/build.sh` adds the image to install, Fedora's kernel (`kernel.sh`), a live initramfs, livesys, and Anaconda with its kickstart (`anaconda.sh`).
4. [Titanoboa](https://github.com/ublue-os/titanoboa) (Universal Blue's live ISO builder, pinned to a commit) squashes it into the ISO.
5. Writes the checksum, signs the ISO with `SIGNING_SECRET`, and keeps all three files as a workflow artifact for 3 days.
6. With *publish* on, and only from `main`, uploads them to Cloudflare R2: the ISO first, then its checksum and signature. Each upload replaces the previous ISO of the same name, so the download links stay the same.

Each ISO takes about 30–40 minutes and is about 6–8 GB.

The installer is adapted from [Bazzite's](https://github.com/ublue-os/bazzite/tree/main/installer) (Apache-2.0). When Bazzite's ISO changes, compare `installer/` with theirs.

### Publishing setup (R2)

The upload step needs:
- repository secrets `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` (an R2 API token with Object Read & Write on the bucket) and `R2_ENDPOINT` (`https://<account id>.r2.cloudflarestorage.com`);
- a repository variable `R2_BUCKET` with the bucket's name.

## Testing an ISO

Download the artifact from the workflow run, then boot it in a UEFI VM with a blank disk, for example:

```bash
virt-install --connect qemu:///session --name redfox-iso-test --memory 8192 --vcpus 4 \
    --disk size=64 --cdrom redfox-os.iso --boot uefi --osinfo fedora-unknown --graphics vnc
```

Check:
- the live session starts and the welcome dialog shows;
- the installer creates the account and finishes;
- the installed system boots and logs in, and Flatpaks arrive;
- `rpm-ostree status` shows `ostree-image-signed:docker://ghcr.io/snakeeyes021/<image>:latest`;
- with Secure Boot on (OVMF's Secure Boot firmware): the ISO starts, and after the MOK enrolment the installed system does too.

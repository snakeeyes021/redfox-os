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

`.github/workflows/build-live-iso.yml` runs in two ways:
- **A published release** (a GitHub release from `main`, not a pre-release) builds all three ISOs and publishes them. The workflow finds the release's commit, waits for main's image build of that commit (BlueBuild tags it `<sha7>-<fedora>`), and builds from exactly those images. The installed system then follows `:latest`. If the images don't appear within 2 hours, or any of the three ISOs fails, nothing is uploaded or deleted and the run is red.
- **By hand** (*Actions › Build live ISOs › Run workflow*): a test build from any tag, with the channel the installed system should follow (`latest` or `unstable`) and one ISO or all three. It's kept as a workflow artifact for 3 days and **never published**.

Each build:
1. Frees the runner's disk, and puts podman's storage on a compressed btrfs file.
2. Pulls the images, accepting only ones signed with `cosign.pub`.
3. Builds the live system from `installer/Containerfile`. `installer/build.sh` adds the image to install, Fedora's kernel (`kernel.sh`), a live initramfs, livesys, and Anaconda with its kickstart (`anaconda.sh`).
4. [Titanoboa](https://github.com/ublue-os/titanoboa) (Universal Blue's live ISO builder, pinned to a commit) squashes it into the ISO.
5. Writes the checksum, signs the ISO with `SIGNING_SECRET`, and keeps all three files as a workflow artifact for 3 days.

Then, for a release only, the publish job (after all three ISOs built):
1. Uploads them to `staging/` in the bucket and checks the sizes. A failure here leaves the published files untouched.
2. Copies the files that were current into `previous/`, replacing what was there.
3. Moves the new ones over the current names: the ISOs first, then the checksums, signatures and `RELEASE` (the release's tag). The names never change, so the download links keep working.
4. Deletes anything else at the top of the bucket.

So the bucket holds the current release and the one before it (about 45 GB, roughly $0.55 a month). The Worker serves the older one at `previous/<file name>` (for example `https://download.redfoxlabs.tech/previous/redfox-os.iso`), for when the current build won't install on a machine. It's an older build, not a stable or long-term one, so the download page and README don't link to it; anywhere it's ever mentioned, it should be described that way. It can also be put back by hand if a release has to be pulled.

Each ISO takes about 30–40 minutes and is about 7–8 GB.

The installer is adapted from [Bazzite's](https://github.com/ublue-os/bazzite/tree/main/installer) (Apache-2.0). When Bazzite's ISO changes, compare `installer/` with theirs.

### Publishing setup (R2)

The upload step needs:
- repository secrets `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` (an R2 API token with Object Read & Write on the bucket) and `R2_ENDPOINT` (`https://<account id>.r2.cloudflarestorage.com`);
- a repository variable `R2_BUCKET` with the bucket's name.

### Downloads (download.redfoxlabs.tech)

The bucket has no public address of its own. Downloads go through a small Worker, `installer/download-worker/`, attached to the custom domain `download.redfoxlabs.tech`, with the bucket bound as `DOWNLOADS`.
- It answers GET and HEAD for a file name: Range requests (one range), `If-Range`, `If-None-Match` and `If-Modified-Since`, with `Content-Length`, `Content-Type`, `Content-Disposition` and an `ETag`. A missing name is 404 and there's no listing; other methods get 405.
- It passes R2's stream straight through, so a 7 GB download uses no more of the Worker's CPU time than a small file (time spent waiting on I/O doesn't count).
- On the Workers Free plan, an account gets 100,000 requests a day; past that Cloudflare answers with error 1027 until midnight UTC. A custom domain has no origin behind it, so nothing gets past the limit. That caps reads at about 3 million a month, inside R2's free 10 million, so the bucket only ever costs its storage.
- `installer/download-worker/test.sh <url> [local copy]` checks it, locally (`wrangler dev` with a local bucket) or live.

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

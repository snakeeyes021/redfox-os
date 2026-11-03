# RedFoxOS ISO: open questions

Status: design notes only, 2026-11-03. No build work yet.

Today the only way to get RedFoxOS is to rebase onto it, from Bazzite, Bluefin or another Fedora Atomic GNOME install. Eventually RedFox wants an ISO of its own. This page collects the questions to answer first.

## What exists already

`.github/workflows/build-iso.yml` builds an ISO with bootc-image-builder (`--type anaconda-iso`, btrfs root), using `disk_config/iso.toml`. It runs after each successful `main` build and by hand.
- Its last runs, on 2026-01-01, failed.
- It patches the image first to drop broken Terra repo files.
- It only keeps the ISOs as Actions artifacts for 7 days, so nothing is published.

## Questions

1. **Builder.** How do the other Universal Blue-family images build ISOs today, and which fits RedFox?
   - **bootc-image-builder's `anaconda-iso`**, the current workflow: an offline Anaconda installer with the image inside.
   - **BlueBuild's own `bluebuild generate-iso`**: wraps an installer builder, and fits the recipe tooling RedFox already uses.
   - **Titanoboa**: Universal Blue's live-ISO builder, as used by the newer Bluefin and Aurora ISOs. It boots into the image, with an installer inside.

   Things to compare: ISO size, build time on a free GitHub runner, and whether the result installs the signed `ghcr.io` image so updates work straight away.
2. **Hosting.**
   - GitHub release assets are limited to 2 GiB per file, and each variant's ISO (main, NVIDIA, NVIDIA legacy) is likely bigger.
   - Options:
     - an ISO that downloads the image during install (small, but needs a network);
     - splitting files (awkward for users);
     - ghcr as an OCI artifact (free, but not a normal download);
     - an object store such as Cloudflare R2 (cheap and no egress fees, but costs something and needs an account);
     - a torrent.
   - Who pays, and the URL users see (redfoxlabs.tech?).
3. **Branding the installer.**
   - Anaconda can be themed (its product name, sidebar art and colours).
   - Bazzite ships its own installer setup.
   - How much RedFox needs to change: the name and the fox at least. Keep it maintainable across Fedora releases.
4. **Secure Boot.**
   - The kernel is signed with Universal Blue's key, so a Secure Boot machine has to enrol that key (`ujust enroll-secure-boot-key`, or the MOK screen at first boot).
   - The installer and its first-boot instructions must make that clear.
   - Does RedFox ever need its own key? Probably not while it uses Bazzite's kernel.
5. **NVIDIA variants.**
   - One ISO per image, so three.
   - Or one ISO that picks the variant from the hardware, as some uBlue images do.
   - The NVIDIA images also need the key enrolment step above.
6. **Testing.**
   - The VM testbed (`tests/vm/`) installs from the Silverblue ISO with a kickstart. An ISO test would boot RedFox's own ISO in a fresh VM instead, unattended through a kickstart.
   - Check that the installed system boots, logs in, updates and rolls back, and that `rpm-ostree status` shows the signed `ghcr.io` image.

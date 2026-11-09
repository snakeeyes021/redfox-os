# How RedFoxOS works

The system is one image that is replaced whole at each update, while your files and apps stay yours.

## One image

RedFoxOS is built on Bazzite and Fedora. Instead of installing and updating thousands of packages one by one on your machine, RedFoxOS is built in advance as a single system image. Every RedFoxOS machine on the same build runs exactly the same system.

The image lives in `/usr`, which is read-only. You can't change it by accident, and nothing you install can break it.

## What's yours

- **Your home folder** (`/home`, which is really `/var/home`) is never touched by updates.
- **Apps** from Bazaar (Flathub), Homebrew and containers live outside the image, so they survive updates. See [Installing apps](manual:installing-apps).
- **`/etc`** holds the machine's settings. Your changes there are kept, and merged with the image's defaults at each update.

## What this means day to day

- Updates happen in the background and take effect when you restart. See [Updates and rolling back](manual:updates).
- If an update goes wrong, the previous system is still there, one choice away.
- You don't install apps with `dnf`. Most come from Bazaar; command-line tools come from Homebrew; anything else goes in a container.

## The first start

On some computers, the first start after installing restarts once by itself, a few minutes in. That's Bazzite's hardware setup adding settings that only some hardware needs, such as AMD graphics, handheld PCs and Microsoft Surface devices. The screen says "Preparing System - Please wait, this may take a while" while it works. Let it finish: the computer comes back to the login screen, and it doesn't happen again.

## Three images

There are three versions of the image, depending on the graphics card:

- **RedFoxOS (AMD & Intel)** (`redfox-os`), for AMD & Intel graphics, and NVIDIA cards older than the GTX 750,
- **RedFoxOS NVIDIA** (`redfox-os-nvidia`), for NVIDIA GTX 16xx, RTX 20xx and newer,
- **RedFoxOS NVIDIA Legacy** (`redfox-os-nvidia-legacy`), for NVIDIA GTX 10xx, 9xx and 750.

You can switch to another one in [Hub › Updates](hub:updates), under System Image.

To see which one you're running:

```sh
rpm-ostree status
```

# Installing apps

Get desktop apps from Bazaar, command-line tools from Homebrew, and anything else in a container; change the system image only as a last resort.

## Desktop apps: Bazaar

**Bazaar** is the app store. It installs apps from [Flathub](https://flathub.org) as Flatpaks, which run alongside the system rather than inside it, are updated with it, and never get in the way of a system update. Look here first.

[Hub › Apps](hub:apps) has RedFox's packs of favourites (Productivity, Creative, Dev and others), ready to tick and install.

To install a Flatpak from a terminal:

```sh
flatpak install flathub org.gnome.Podcasts
```

## Command-line tools: Homebrew

Homebrew installs command-line tools outside the system image, without touching it. It has most tools you'd otherwise get from `dnf` or `apt`:

```sh
brew install gh
brew search ripgrep
```

RedFoxOS's updates, automatic or from [Hub › Updates](hub:updates), keep Homebrew tools up to date along with everything else.

## Anything else: Distrobox

**Distrobox** runs another Linux system (Fedora, Ubuntu, Arch and others) in a container that shares your home folder, so its programs feel like part of your desktop. Inside it you use that system's own package manager. It's the place for software only packaged as `.rpm` or `.deb`, or that needs a particular distribution.

```sh
distrobox create --name ubuntu --image ubuntu:24.04
distrobox enter ubuntu
```

Inside the box, `sudo apt install` works as usual. To put an app from the box in your app grid, run `distrobox-export --app` with its name, from inside the box.

**DistroShelf**, in the app grid, does the same with buttons.

## Last resort: rpm-ostree install

`rpm-ostree install` adds ("layers") a Fedora package on top of the system image. Use it only for things that can't work any other way, such as drivers or tools that must run as part of the system.

Each layered package:

- makes every update slower, because it's reapplied each time,
- can stop updates altogether when it conflicts with a newer image,
- needs a restart before you can use it.

```sh
rpm-ostree install some-package
```

To see what you've layered, and remove it again:

```sh
rpm-ostree status
rpm-ostree uninstall some-package
```

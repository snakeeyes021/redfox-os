# Updates and rolling back

RedFoxOS updates itself every day, applies the update when you restart, and keeps the previous system in case you need it.

## Automatic updates

Once a day, RedFoxOS downloads the newest image in the background and prepares it for the next start. The same run updates your Flatpak apps and Homebrew tools. Your current system keeps running unchanged until then. **Restart to apply the update.** There's no rush: you can carry on working, and the new system is used the next time you start the computer.

[Hub › Updates](hub:updates) shows how this is going, under **Automatic Updates**:

- **Update Automatically** turns automatic updates on or off. Changing it asks for your password.
- **Update At** is the hour they run: 4:00 by default. To choose another hour, pick it here: for example, an evening hour if you switch the computer off at night, so the update is ready when you start it in the morning. If the computer is off or asleep at that hour, the update runs soon after it starts.
- **Last Automatic Update** is when it last ran, and says so if it didn't finish. An update that doesn't finish tries again by itself.
- **Next Automatic Update** is when it runs next.

To update now, open [Hub › Updates](hub:updates) and choose **Update Now**. It updates the system, your Flatpak apps, Homebrew tools, firmware and RedFox's own apps. When a new system is ready, a **Restart…** button appears; it starts the new system. If only apps were updated, there's nothing to restart for.

## Rolling back

Every update keeps the system you had before it. If something stopped working after an update, go back to it:

- **In [Hub › Updates](hub:updates)**, under **Go Back**: choose **Go Back…** next to **Previous System**, then restart. Before the first update there's no previous system, so the button can't be used yet.
- **At the boot menu.** Restart and pick the second RedFoxOS entry. This boots the previous system once; the next restart goes back to the newest. If the menu doesn't show, press `Esc` a few times as the computer starts.
- **In a terminal**, then restart:

```sh
rpm-ostree rollback
```

Rolling back only changes the system image. Your files, settings and apps are left as they are. The next automatic update moves you forward again; to stay on an older build, see **Going back further** below.

## Stable and unstable

RedFoxOS has two channels:

- **Stable** (`latest`) is the default. Changes reach it after they've been tried on Unstable.
- **Unstable** (`unstable`) is built every day from the newest work. It gets fixes and features first, and sometimes new bugs.

To switch, choose **Stable** or **Unstable** under **System Image** in [Hub › Updates](hub:updates), then restart. **Go Back › This System** shows the build you're running now.

In a terminal, to see your channel and the builds kept for rollback:

```sh
redfox-rollback-helper current
```

To switch channel, then restart:

```sh
redfox-rollback-helper rebase unstable
redfox-rollback-helper rebase latest
```

## Going back further

To go back more than one update, pick an older build by its date. In [Hub › Updates](hub:updates), choose **Go Back › Other Builds**: it lists the recent builds of each channel, and **Switch…** next to one moves to it at the next restart.

A build picked this way stays put and doesn't update. While you're on one, **Fixed Build** shows under **System Image**; choose **Stable** or **Unstable** there to follow updates again.

In a terminal, list the recent builds of your channel:

```sh
redfox-rollback-helper list
```

Then rebase to one of them, for example `redfox-rollback-helper rebase 20261101`. Rebase to `latest` or `unstable` to follow updates again.

## Graphics

RedFoxOS comes in three images, one for each kind of graphics:

- **RedFoxOS (AMD & Intel)**, for AMD & Intel graphics, and for older NVIDIA cards that NVIDIA's drivers no longer support: the GTX 600 series and most of the 700 series, such as the GTX 760, 770 and 780.
- **RedFoxOS NVIDIA**, for GTX 16xx, RTX 20xx and newer.
- **RedFoxOS NVIDIA Legacy**, for GTX 10xx, 9xx, 750 and 745.

Each follows either channel. To change image, pick it under **System Image › Graphics** in [Hub › Updates](hub:updates). The one that suits this computer's graphics is marked **Works best on your machine**. In a terminal:

```sh
redfox-rollback-helper switch-image
```

Only pick the one that matches your graphics card: the wrong drivers can leave the screen blank. If that happens, pick the previous system in the boot menu.

## Feature branches

Developers can try work in progress before it reaches Unstable. While a feature branch has a test build, it is listed under **Advanced › Feature Branches** in [Hub › Updates](hub:updates). These builds are unsupported and don't update. To get back, pick the previous system in the boot menu or use **Go Back**, then choose a channel again.

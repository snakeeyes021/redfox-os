# Updates and rolling back

RedFoxOS updates itself every day, applies the update when you restart, and keeps the previous system in case you need it.

## Automatic updates

Once a day, RedFoxOS downloads the newest image in the background and prepares it for the next start. Your current system keeps running unchanged until then. **Restart to apply the update.** There's no rush: you can carry on working, and the new system is used the next time you start the computer.

To update now, open [Hub › Updates](hub:updates) and choose **Update Now**. It updates the system, your Flatpak apps, Homebrew tools, firmware and RedFox's own apps. When it's done, **Restart** starts the new system.

## Rolling back

Every update keeps the system you had before it. If something stopped working after an update, go back to it:

- **At the boot menu.** Restart and pick the second RedFoxOS entry. This boots the previous system once; the next restart goes back to the newest. If the menu doesn't show, press `Esc` a few times as the computer starts.
- **In [Hub › Updates](hub:updates).**
- **In a terminal**, then restart:

```sh
rpm-ostree rollback
```

Rolling back only changes the system image. Your files, settings and apps are left as they are. The next automatic update moves you forward again; to stay on an older build, see **Going back further** below.

## Stable and unstable

RedFoxOS has two channels:

- **`latest`** is the stable channel, and the default. Changes reach it after they've been tried on `unstable`.
- **`unstable`** is built every day from the newest work. It gets fixes and features first, and sometimes new bugs.

To see your channel, and the builds kept for rollback:

```sh
redfox-rollback-helper current
```

To switch channel, then restart:

```sh
redfox-rollback-helper rebase unstable
redfox-rollback-helper rebase latest
```

## Going back further

To go back more than one update, pick an older build by its date or commit. List the recent builds of your channel:

```sh
redfox-rollback-helper list
```

Then rebase to one of them, for example `redfox-rollback-helper rebase 20261101`. A build picked this way stays put and doesn't update. Rebase to `latest` or `unstable` to follow updates again.

## Graphics

RedFoxOS comes in three images, one for each kind of graphics:

- **Mainline**, for Intel and AMD graphics.
- **NVIDIA**, for GTX 16xx, RTX 20xx and newer.
- **NVIDIA legacy**, for GTX 10xx and older.

Each follows either channel. To change image, pick it under **Graphics** in [Hub › Updates](hub:updates), or in a terminal:

```sh
redfox-rollback-helper switch-image
```

Only pick the one that matches your graphics card: the wrong drivers can leave the screen blank. If that happens, pick the previous system in the boot menu.

## Feature branches

Developers can try work in progress before it reaches `unstable`. While a feature branch has a test build, it is listed under **Advanced › Feature Branches** in [Hub › Updates](hub:updates). These builds are unsupported and don't update. To get back, pick the previous system in the boot menu or use **Go Back**, then choose a channel again.

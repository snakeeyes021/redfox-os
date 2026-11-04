# Updates and rolling back

RedFoxOS updates itself every day, applies the update when you restart, and keeps the previous system in case you need it.

## Automatic updates

Once a day, RedFoxOS downloads the newest image in the background and prepares it for the next start. Your current system keeps running unchanged until then. **Restart to apply the update.** There's no rush: you can carry on working, and the new system is used the next time you start the computer.

To update now, open **RedFox Updater** from the app grid. It updates the system, your Flatpak apps, Homebrew tools, firmware and RedFox's own apps, then offers to restart. Or use [Hub › Updates](hub:updates).

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

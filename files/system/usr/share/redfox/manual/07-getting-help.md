# Getting help

How to find out what went wrong, and where to report a problem with RedFoxOS.

## First steps

- **Did it start after an update?** Roll back and see whether the problem goes away. See [Updates and rolling back](manual:updates).
- **Is it one app?** Flatpak apps from Bazaar are made by their own developers, not RedFoxOS. Check the app's page in Bazaar for where to report it.

## Reading the logs

The **Logs** app, in the app grid, shows the system's messages, newest first, with a search box.

In a terminal, `journalctl` does the same. Errors since this start:

```sh
journalctl -b -p err
```

Errors from the start before this one, useful after a crash or a failed update:

```sh
journalctl -b -1 -p err
```

Messages from one service, such as the automatic update:

```sh
journalctl -u uupd
```

Messages from your own session (the desktop and your apps):

```sh
journalctl --user -b
```

## Reporting a problem

Report RedFoxOS problems on GitHub: [github.com/snakeeyes021/redfox-os/issues](https://github.com/snakeeyes021/redfox-os/issues). Search there first, in case it's already known.

A good report says what you did, what you expected and what happened instead. Include the image you're running, from:

```sh
rpm-ostree status
```

and paste any error lines from the logs.

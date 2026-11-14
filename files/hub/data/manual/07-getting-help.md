# Getting help

How to find out what went wrong, and where to report a problem with RedFoxOS.

## First steps

- **Did it start after an update?** Roll back and see whether the problem goes away. See [Updates and rolling back](manual:updates).
- **Is it one app?** Flatpak apps from Bazaar are made by their own developers, not RedFoxOS. Check the app's page in Bazaar for where to report it.

## Fixes in RedFox Hub

At the top of this Manual, **Something not working?** lists quick fixes for common problems. **Collect Logs** and **Restart into Firmware Settings** run from there; the others open the part of Hub where they are, next to the settings they're about. Only the ones that apply to this computer are shown.

- **Collect Logs** saves this computer's logs and system details in one zip in your Downloads folder, for someone helping you. Your name, the computer's name, email addresses, network names, serial numbers and similar details are taken out where RedFox can find them, and nothing is uploaded: you choose whom to send it to. Look through it before you post it anywhere public. In a terminal, `redfox-logs` does the same.
- **Restart Audio**, in [Hub › Settings](hub:settings), under **Sound & Music**, if sound stops, or a speaker or headset doesn't show up.
- **Stop Stuck Windows Games** and **Reset Steam**, in [Hub › Software](hub:apps), on the **Gaming** tab, for a game that won't close or start again, and for Steam itself.
- **Update NVIDIA Libraries for Flatpak Apps**, in [Hub › Updates](hub:updates), on computers with NVIDIA graphics, if Flatpak apps lose graphics acceleration.
- **Restart into Firmware Settings**, on computers that start with UEFI, for the computer's own setup screen: boot order, virtualization or Secure Boot. Holding `Shift` in the power menu does the same.

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

A good report says what you did, what you expected and what happened instead. The easiest way to include the details is the zip from **Collect Logs**: it already has the image you're running, the state of updates and the system's logs. Attach it to the report.

Without it, include the image you're running, from:

```sh
rpm-ostree status
```

and paste any error lines from the logs.

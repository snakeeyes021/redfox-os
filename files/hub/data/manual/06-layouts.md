# Layouts

RedFoxOS has six desktop layouts, and you can switch between them at any time without logging out.

## Choosing one

Open [Hub › Settings › Layout](hub:settings/layout) and pick a card. The desktop changes straight away, behind the window, so you can try each one. Your apps and windows stay open.

Switching layout puts the dock or taskbar's own settings back to that layout's defaults, so anything you changed in the dock's or taskbar's settings has to be set again afterwards.

## The six layouts

- **RedFox.** A floating dock on the left on big screens; the GNOME dash on small ones. The default.
- **GNOME.** Plain GNOME: the top bar, with the dash in the overview.
- **Ubuntu.** A full-height dock on the left, always visible.
- **Cal.** A floating dock along the bottom, window buttons on the left.
- **Wash.** One taskbar along the bottom, with the start menu and apps centred.
- **Nostalgia.** One taskbar along the bottom: start menu and apps on the left, clock on the right.

## Floating dock settings

Below the cards, the **Floating Dock** settings apply to the layouts whose dock floats:

- **Gap to the Screen Edge** is the space between the dock and the edge of the screen, in the RedFox and Cal layouts.
- **Dock on Screens at Least** is the screen width from which the RedFox layout shows its dock. On narrower screens it uses the plain GNOME dash instead.

## Clicking an open app

What happens when you click an app that's already open, in the dock or the taskbar, is set in [Hub › Settings](hub:settings) under **Clicking an Open App**: for example, show its windows' previews, spread its windows out, or bring it to the front. Each layout starts with the behaviour of the system it's modelled on, and switching layout sets it back to that. The GNOME layout has no dock, so the setting doesn't apply there.

## From a terminal

```sh
redfox-layout list
redfox-layout get
redfox-layout set cal
```

Use the names in lower case: `redfox`, `gnome`, `ubuntu`, `cal`, `wash` and `nostalgia`.

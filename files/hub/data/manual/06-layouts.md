# Layouts

RedFoxOS has six desktop layouts, and you can switch between them at any time without logging out.

## Choosing one

Open [Hub › Desktop › Layout](hub:desktop/layout) and pick a card. The desktop changes straight away, behind the window, so you can try each one. Your apps and windows stay open.

Switching layout puts the dock or taskbar's own settings back to that layout's defaults, so anything you changed in the dock's or taskbar's settings has to be set again afterwards.

## The six layouts

- **RedFox.** A floating dock on the left on big screens; the GNOME dash on small ones. The default.
- **GNOME.** Plain GNOME: the top bar, with the dash in the overview.
- **Ubuntu.** A full-height dock on the left, always visible.
- **Cal.** A floating dock along the bottom, window buttons on the left.
- **Wash.** One taskbar along the bottom, with the start menu and apps centred.
- **Nostalgia.** One taskbar along the bottom: start menu and apps on the left, clock on the right.

## Dock and gaps

Below the cards are the **Dock and Gaps** settings:

- **Gaps** is the space between tiled windows and around them, in every layout, and also between a floating dock (RedFox, Cal) and the edge of the screen. It's one setting for all of them, so tiled windows and the dock line up. Changing the gaps in the tiling settings changes it too, and switching layout keeps it.
- **Dock on Screens From** is the screen size, in inches measured across, from which the RedFox layout shows its dock: 15 to start with. On smaller screens it uses the plain GNOME dash instead. A screen that doesn't say how big it is (some projectors, for example) gets the dock when it's at least 1600 pixels wide.
- **Show the Dock on Small Screens Too** keeps the RedFox layout's dock on every screen, whatever its size.

Changes apply straight away, and again whenever you plug in or unplug a screen. When the dock comes or goes, tiled windows move to fill their tiles in the space there is now.

The two dock-size settings are only for the RedFox layout, so they're greyed out in the others.

## Clicking an open app

What happens when you click an app that's already open, in the dock or the taskbar, is set in [Hub › Desktop](hub:desktop) under **Clicking an Open App**: for example, show its windows' previews, spread its windows out, or bring it to the front. Each layout starts with the behaviour of the system it's modelled on, and switching layout sets it back to that. The GNOME layout has no dock, so the setting doesn't apply there.

## From a terminal

```sh
redfox-layout list
redfox-layout get
redfox-layout set cal
```

Use the names in lower case: `redfox`, `gnome`, `ubuntu`, `cal`, `wash` and `nostalgia`.

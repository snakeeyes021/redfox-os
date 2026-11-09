# Layouts

RedFoxOS has six desktop layouts, and you can switch between them at any time without logging out.

## Choosing one

Open [Hub › Settings › Layout](hub:settings/layout) and pick a card. The desktop changes straight away, behind the window, so you can try each one. Your apps and windows stay open.

## The six layouts

- **RedFox.** A floating dock on the left on big screens; the GNOME dash on small ones.
- **GNOME.** Plain GNOME: the top bar, with the dash in the overview. The default.
- **Ubuntu.** A full-height dock on the left, always visible.
- **Cal.** A floating dock along the bottom, window buttons on the left.
- **Wash.** One taskbar along the bottom, with the start menu and apps centred.
- **Nostalgia.** One taskbar along the bottom: start menu and apps on the left, clock on the right.

Below the cards, the Layout page also sets the gap round floating docks, and the screen width from which the RedFox layout shows its dock.

## From a terminal

```sh
redfox-layout list
redfox-layout get
redfox-layout set cal
```

Use the names in lower case: `redfox`, `gnome`, `ubuntu`, `cal`, `wash` and `nostalgia`.

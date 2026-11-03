# Screenshot markup: Satty or a small RedFox app

Status: evaluation for Matt, 2026-11-03. Nothing is built.

Matt wants quick, easy markup for screenshots. Gradia comes closest, but it does too much. Capturing stays with GNOME's own screenshot tool. The app should do this, and nothing more:

1. Open from the clipboard, a file, or GNOME's "screenshot taken" notification
2. Crop and rotate
3. Pen and highlighter, with colour and size
4. Arrow and rectangle
5. Text box
6. Blur or pixelate (to redact)
7. Undo and redo
8. Copy to clipboard (the main way out) and save

## Satty, as it is today

[Satty](https://github.com/Satty-org/Satty) is a screenshot annotation tool. Version 0.22.0 (2026-08-03) was tried in the `redfox-test` VM from its release Flatpak, then removed. Nothing was installed on Matt's machine. Screenshots on the preview: `satty-markup-vm.png` (arrow and rectangle on a screenshot) and `satty-toolbar.png`.

- **Licence:** MPL-2.0. That's a file-level copyleft: we may build and ship it, and our own files can carry any licence, but changes to Satty's own files stay MPL-2.0 and must be published.
- **Stack:** Rust, GTK 4 through relm4 (with libadwaita), drawn with femtovg on OpenGL. Active: commits weekly, about 2,500 stars.
- **How it looks:** a plain GTK window titled "satty" with two floating toolbars, not a libadwaita window with a header bar. It looks tidy but not like a GNOME app. One open issue reports blank toolbar icons on GTK 4.22 (#651); the Flatpak's GNOME 49 runtime isn't affected.
- **Wayland and the sandbox:**
  - Opening a file works. Copying works through GTK's own clipboard, and the copied image survived Satty closing, because GNOME keeps the clipboard.
  - The Flatpak asks for a lot: the whole home folder, network access, and both X11 and Wayland. Flathub would ask for narrower permissions.
- **Flathub:** not there. Upstream builds a `.flatpak` for each GitHub release. The Flathub issue (#237) is open. The maintainers' stance is "we only ship source and binaries; others may package". The latest step is checking that Flathub's AI-use policy matches Satty's own.

### Against Matt's list

| # | Feature | Satty 0.22 |
| --- | --- | --- |
| 1 | Open from file / clipboard / notification | File: **yes**. Clipboard: **no** in the released Flatpak; `--from-clipboard` arrives in the next release and runs `wl-paste`, which isn't in the sandbox. Notification: **no** (no app can do this alone; see below). |
| 2 | Crop / rotate | Crop: **yes**. Rotate: **no** (issue #130, open since 2024). |
| 3 | Pen, highlighter, colour, size | **Yes**: pen, brush and highlighter, a colour palette, S/M/L sizes and a scale factor. |
| 4 | Arrow, rectangle | **Yes**. |
| 5 | Text box | **Yes**. An open issue reports trouble typing accented letters (#531). |
| 6 | Blur, pixelate | **Yes**, both. |
| 7 | Undo, redo | **Yes**. |
| 8 | Copy, save | **Yes**. Copy is Ctrl+C or a button; it can also copy on every change. |
| | Nothing more | **No**. Line, ellipse, numbered markers and an image-insert tool are always in the toolbar, and its config can't hide individual tools. |

So Satty covers about six of the eight. It's missing rotate and opening from the clipboard, and it shows extra tools.

## Opening from GNOME's notification (needed by every route)

GNOME's screenshot tool copies each shot to the clipboard and shows a notification with one action, "Show in Files" (`js/ui/screenshot.js`, `_storeScreenshot`). Apps can't add actions to it. But RedFox already ships a GNOME Shell extension, the layout helper, which can add a **"Mark up"** button to that notification and open the markup app on the saved file. Because the shot is on the clipboard too, "open from clipboard" covers the same moment if the notification is missed.

## The three routes

### A. Ship Satty as it is

Either use our own install of its release Flatpak through `update-redfox-apps`, or help it onto Flathub upstream.

- **For:** nothing to write, and it's mature and actively developed. Flathub would be the cleanest home for everyone.
- **Against:**
  - Two of the eight features are missing (rotate, clipboard open in the Flatpak), and the extra tools can't be hidden.
  - It isn't a libadwaita-style window, and the permissions are broad.
  - Flathub is the maintainers' call. Their stance and the AI-policy question mean it may not happen soon.

### B. A light RedFox fork or configuration

Configuration alone can't remove tools or add rotate. So this means a fork:
- add rotate;
- open from the clipboard through GTK, not `wl-paste`;
- an option to hide tools;
- a libadwaita header bar;
- narrower permissions.

The licence allows it, and the changes would be published as MPL-2.0.

- **For:** keeps Satty's drawing engine.
- **Against:**
  - Rust, relm4 and femtovg would be a new stack for RedFox.
  - Keeping a fork of a fast-moving project means regular merge work.
- **Better than forking:** offer the useful pieces upstream (rotate, GTK clipboard open, tool visibility). If they land, this becomes route A.

### C. Our own small app in the RedFox Hub family

Python, GTK 4 and libadwaita, like Hub, Thirties and Pianola. It covers exactly the eight features above, so the window shows nothing more:
- a drawing area with Cairo for pen, highlighter, arrow, rectangle and text;
- pixelate by scaling a region down and up, and blur with a box filter;
- crop and rotate on the image;
- an undo stack;
- `Gdk.Clipboard` to read and write images.

The "Mark up" notification button comes from the layout helper extension.

- **For:**
  - Exactly Matt's list and the GNOME look.
  - Narrow permissions: no home folder access needed beyond the file portal.
  - The same stack and release path as the other RedFox apps.
- **Against:** it's new code. Roughly **2–4 weeks** for one developer to get a polished first version, mostly the drawing and text editing.

## Recommendation

**Route C: a small RedFox app**, plus the "Mark up" button in the layout helper.

Matt asked for this list "and nothing more". Satty can't be trimmed to that without a fork. It also lacks two of the eight features and doesn't look like a GNOME app, and the notification integration has to be RedFox's work whichever route we take.

If Matt wants something usable before then, route A's Satty Flatpak (installed per user from its GitHub release) is a reasonable stop-gap, with screenshots opened by file. Sending rotate and GTK clipboard support to Satty upstream is a nice extra but not needed for RedFox's plan.

Working name: **RedFox Markup** (`tech.redfoxlabs.Markup`), Matt's to change.

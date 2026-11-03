# Mailspring in RedFoxOS: the Adwaita theme and its companion plugin

Status: on `feat/mailspring-adwaita`, not merged. The comparison page (vanilla, our theme at each iteration, and a native GTK 4 mock) is built by `tools/mailspring-mock/`; see `iterations.json` there for what each round changed.

## What ships

- **RedFox Adwaita Light and Dark**, two Mailspring theme packages, written from scratch. Mailspring's Automatic theme switches between them as GNOME switches between light and dark, and they follow the GNOME accent colour.
- **GNOME's Adwaita icons** in place of Mailspring's own, in the header bar, the folder sidebar and the message view. See "Icons" below.
- **RedFox GNOME integration**, a small plugin (`redfox-gnome-integration`, plain JavaScript). It puts the window buttons where GNOME's `button-layout` setting says: which side, which buttons, and in what order. It reads the setting through the desktop portal, since Mailspring runs in a Flatpak, and follows changes live.
- **Adwaita Sans and Mono in the user's font folder.** Flatpaks on the Freedesktop 26.08 runtime can't see system fonts (see `fix/flatpak-system-fonts`). Once that branch fixes it for every Flatpak, this copy can go.

The login hook `70-mailspring-theme.sh` installs all of it into Mailspring's own folder. A light or dark theme the user picked is left alone.

## What a plugin can and can't do

Mailspring loads JavaScript packages from its `packages` folder (no developer mode needed). They can add React components into named slots, inject styles, and run commands. Here's what that means for the gaps between our theme and a native libadwaita app:

| Gap | Plugin? | Notes |
| --- | --- | --- |
| Window buttons follow GNOME's layout | **Done** (v4) | Reads `org.gnome.desktop.wm.preferences button-layout` through `org.freedesktop.portal.Settings`, and watches its `SettingChanged` signal. Tested with right, left, close-only on either side, and none. |
| Reply / Reply all / Forward in the header bar | **Done** (v5) | Registered in Mailspring's thread-toolbar slot for plugins (`ThreadActionsToolbarButton`, the one archive and trash use), calling Mailspring's own `composeReply` / `composeForward`. Mailspring decides the order inside that slot, so the group sits after its own buttons, not first. |
| Avatars in message headers | Feasible, medium | The `MessageHeader` and `message:BodyHeader` slots take components. Initials avatars are easy; photos would need a contacts source. |
| A thread-list header ("Inbox · 5 unread") | Possible but fragile | There's no slot for it, so it would mean adding DOM nodes by hand, which a Mailspring update can break. |
| The contact panel on the right | Already a setting | Mailspring can hide its sidebar; CSS could too. It's a feature, so we leave the choice to the user. |
| Row heights, the split header layout | No | The thread list is virtualised with row heights set in code, and the column layout is Mailspring's own. |
| Rounded window corners, native GTK menus and dialogs | No | Electron's frame and HTML widgets. |

**Costs of plugins:** plugins run with Mailspring's own access, and they use Mailspring's internal APIs, which can change between releases. Each one needs re-testing when Mailspring updates. The plugin is kept small (see "Effort and risk" below), and if it ever breaks, Mailspring keeps the theme's defaults.

**How the button layout is read:**
- **Inside the Flatpak, through the Settings portal**, the way GTK apps do: `org.freedesktop.portal.Settings` exposes `org.gnome.desktop.wm.preferences button-layout`, and the plugin watches the portal's `SettingChanged` signal, so changes apply live.
- **Ruled out:** the alternatives were a login hook writing a generated stylesheet for the current layout, or a user service running `gsettings monitor` to regenerate it. They aren't needed now that the portal works, and they'd only apply at start-up unless Mailspring reloaded its theme.

**Plugins and shared modules:** a plugin must take React and Mailspring's APIs from `mailspring-exports`. A plain `require('react')` doesn't resolve from a user package, and the error stops the whole plugin from loading.

**Effort and risk:**
- The plugin is about 150 lines of plain JavaScript in two files: button layout and Reply/Forward. It took about half a day, mostly testing.
- It uses only documented plugin slots and actions (`ComponentRegistry`, `Actions`, `RetinaImg`). Those have been stable across Mailspring releases, but they're internal APIs, not a promised interface.
- Each Mailspring update needs a quick check: buttons in place, Reply opens a draft.
- If a release breaks the plugin, Mailspring logs "Failed to activate plugin" and carries on. The theme's defaults (buttons on the right, Mailspring's own reply controls) still work.

**Recommendation:** keep both parts of the plugin. Initials avatars are the next cheap one, through a supported slot. Skip the thread-list header, which would need fragile DOM changes.

## Icons

Mailspring's icons are swapped for GNOME's Adwaita symbolic icons (v6). The rules are in `adwaita-icons.less`, which the login hook copies into both theme packages.

**Where they come from:** the system's own icon theme, not copies in this repo. Inside Mailspring's Flatpak the host's icon themes are mounted at `/run/host/share/icons/`. The Freedesktop 26.08 runtime has no Adwaita of its own (only `hicolor`), so the plugin looks in `/run/host/share/icons/Adwaita/symbolic/` first and in the runtime's `/usr/share/icons/Adwaita/symbolic/` second, in case a later runtime ships one.

**How:** the plugin (`lib/icons.js`) looks up each icon the stylesheet uses. For each one it finds, it sets the CSS variable `--adw-icon-NAME` to the file and adds the class `adw-icon-NAME` to `<html>`. Each rule draws its icon as a 16 px mask filled with the theme's text colour, and only under that class. So if an icon is missing (say an Adwaita release renames it), or the plugin is off, Mailspring's own icon stays: no empty box. The icon list in `icons.js` must match the stylesheet's.

**Colours:** the theme's text colour in light and dark; the accent for "on" states (a starred thread, the contact sidebar while it's shown); dimmed for the "Write a reply…" placeholder and the thread list's attachment and forwarded marks.

| Where | Mailspring's icon | Adwaita icon |
| --- | --- | --- |
| Header bar | Compose | `mail-message-new-symbolic` |
| | Search, clear search | `system-search-symbolic`, `edit-clear-symbolic` |
| | Archive | `package-x-generic-symbolic` (Adwaita has no archive icon) |
| | Trash | `user-trash-symbolic` |
| | Star / Unstar | `starred-symbolic` (accent when starred) |
| | Mark as unread / read | `mail-unread-symbolic` / `mail-read-symbolic` |
| | Move to folder, labels | `folder-symbolic`, `user-bookmarks-symbolic` |
| | Snooze, spam, not spam | `alarm-symbolic`, `mail-mark-junk-symbolic`, `mail-mark-notjunk-symbolic` |
| | Reply, Reply all, Forward | `mail-reply-sender-symbolic`, `mail-reply-all-symbolic`, `mail-forward-symbolic` |
| | Contact sidebar | `sidebar-show-right-symbolic` |
| | Menu | `open-menu-symbolic` |
| | Back, previous / next thread | `go-previous-symbolic`, `go-up-symbolic` / `go-down-symbolic` |
| Folder sidebar | Inbox | `folder-download-symbolic` (Adwaita has no `mail-inbox-symbolic`) |
| | Unread, Starred, Drafts, Sent | `mail-unread-symbolic`, `starred-symbolic`, `document-edit-symbolic`, `mail-send-symbolic` |
| | Trash, Archive, Spam / Junk, Important | `user-trash-symbolic`, `package-x-generic-symbolic`, `mail-mark-junk-symbolic`, `mail-mark-important-symbolic` |
| | Folder, label | `folder-symbolic`, `user-bookmarks-symbolic` |
| | Snoozed, Reminders | `alarm-symbolic`, `appointment-soon-symbolic` |
| | Account menu arrow | `pan-down-symbolic` |
| Message | Print | `document-print-symbolic` |
| | Light / dark email view (the bulb) | `weather-clear-night-symbolic` to go dark, `display-brightness-symbolic` to go light |
| | Pop out | `window-new-symbolic` |
| | Reply button and its menu arrow | `mail-reply-sender-symbolic`, `pan-down-symbolic` |
| | Reply menu: Reply, Reply all, Forward | `mail-reply-sender-symbolic`, `mail-reply-all-symbolic`, `mail-forward-symbolic` |
| | "Write a reply…" | `mail-reply-sender-symbolic` / `mail-reply-all-symbolic` |
| | Find in thread: previous, next, close | `go-up-symbolic`, `go-down-symbolic`, `window-close-symbolic` |
| | Attachments: paperclip, download, preview, remove | `mail-attachment-symbolic`, `folder-download-symbolic`, `view-reveal-symbolic`, `window-close-symbolic` |
| Thread list | Attachment, replied, forwarded, starred | `mail-attachment-symbolic`, `mail-replied-symbolic`, `mail-forward-symbolic`, `starred-symbolic` (accent) |
| | Star on hover | `non-starred-symbolic` |
| | Hover actions: archive, trash, snooze | `package-x-generic-symbolic`, `user-trash-symbolic`, `alarm-symbolic` |
| | Draft | `document-edit-symbolic` |

**Left as Mailspring's:** the thread list's unread dot; the message's actions menu button (Mailspring keeps it invisible); expand / collapse all (shown only for threads of several messages; Adwaita has no clear match); file-type icons on attachments; the composer's own toolbar; the sending spinner.

**Licence:** the icons are from adwaita-icon-theme (the GNOME Project), under CC BY-SA 3.0 or LGPL-3.0. RedFox doesn't copy or ship them; it loads the files the system already has.

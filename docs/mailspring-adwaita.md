# Mailspring in RedFoxOS: the Adwaita theme and its companion plugin

Status: on `feat/mailspring-adwaita`, not merged. The comparison page (vanilla, our theme at each iteration, and a native GTK 4 mock) is built by `tools/mailspring-mock/`; see `iterations.json` there for what each round changed.

## What ships

- **RedFox Adwaita Light and Dark**, two Mailspring theme packages, written from scratch. Mailspring's Automatic theme switches between them as GNOME switches between light and dark, and they follow the GNOME accent colour.
- **RedFox GNOME integration**, a small plugin (`redfox-gnome-integration`, plain JavaScript). It puts the window buttons where GNOME's `button-layout` setting says: which side, which buttons, and in what order. It reads the setting through the desktop portal, since Mailspring runs in a Flatpak, and follows changes live.
- **Adwaita Sans and Mono in the user's font folder.** Flatpaks on the Freedesktop 26.08 runtime can't see system fonts (see `fix/flatpak-system-fonts`). Once that branch fixes it for every Flatpak, this copy can go.

The login hook `70-mailspring-theme.sh` installs all of it into Mailspring's own folder. A light or dark theme the user picked is left alone.

## What a plugin can and can't do

Mailspring loads JavaScript packages from its `packages` folder (no developer mode needed). They can add React components into named slots, inject styles, and run commands. Here's what that means for the gaps between our theme and a native libadwaita app:

| Gap | Plugin? | Notes |
| --- | --- | --- |
| Window buttons follow GNOME's layout | **Done** (v4) | Reads `org.gnome.desktop.wm.preferences button-layout` through `org.freedesktop.portal.Settings`, and watches its `SettingChanged` signal. Tested with right, left, close-only on either side, and none. |
| Reply / Reply all / Forward in the header bar | Feasible, small | The thread toolbar has a slot for plugin buttons (`ThreadActionsToolbarButton`), as archive and trash use. The buttons call Mailspring's own actions. |
| Avatars in message headers | Feasible, medium | The `MessageHeader` and `message:BodyHeader` slots take components. Initials avatars are easy; photos would need a contacts source. |
| A thread-list header ("Inbox · 5 unread") | Possible but fragile | There's no slot for it, so it would mean adding DOM nodes by hand, which a Mailspring update can break. |
| The contact panel on the right | Already a setting | Mailspring can hide its sidebar; CSS could too. It's a feature, so we leave the choice to the user. |
| Row heights, the split header layout | No | The thread list is virtualised with row heights set in code, and the column layout is Mailspring's own. |
| Rounded window corners, native GTK menus and dialogs | No | Electron's frame and HTML widgets. |

**Costs of plugins:** plugins run with Mailspring's own access, and they use Mailspring's internal APIs, which can change between releases. Each one needs re-testing when Mailspring updates. The button-layout plugin is deliberately small, under 100 lines, with no React, only styles. If it ever breaks, Mailspring keeps the theme's default (right, GNOME order).

**Recommendation:** keep the button-layout plugin. Add the Reply/Forward header buttons next, since they're small and use a supported slot. Skip the fragile ones.

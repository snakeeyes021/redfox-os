// GNOME's Adwaita symbolic icons for the RedFox Adwaita theme. The theme's
// adwaita-icons.less draws each icon as a mask from --adw-icon-NAME, but only
// under the class adw-icon-NAME on <html>. This sets both for every icon whose
// SVG is found, so an icon that's missing (or a system without Adwaita) keeps
// Mailspring's own image instead of an empty box.
//
// The SVGs come from the system's icon theme, not from this package. Inside
// Mailspring's Flatpak the host's icon themes are mounted at
// /run/host/share/icons; the Freedesktop runtime has no Adwaita of its own,
// but it's checked second in case a later runtime adds one.
const fs = require('fs');
const path = require('path');

const ROOTS = ['/run/host/share/icons/Adwaita/symbolic', '/usr/share/icons/Adwaita/symbolic'];
const STYLE_ID = 'redfox-adwaita-icons';

// Every icon adwaita-icons.less uses. Keep the two lists in step.
const ICONS = [
  'alarm-symbolic',
  'appointment-soon-symbolic',
  'display-brightness-symbolic',
  'document-edit-symbolic',
  'document-print-symbolic',
  'edit-clear-symbolic',
  'folder-download-symbolic',
  'folder-symbolic',
  'go-down-symbolic',
  'go-previous-symbolic',
  'go-up-symbolic',
  'mail-attachment-symbolic',
  'mail-forward-symbolic',
  'mail-mark-important-symbolic',
  'mail-mark-junk-symbolic',
  'mail-mark-notjunk-symbolic',
  'mail-message-new-symbolic',
  'mail-read-symbolic',
  'mail-replied-symbolic',
  'mail-reply-all-symbolic',
  'mail-reply-sender-symbolic',
  'mail-send-symbolic',
  'mail-unread-symbolic',
  'non-starred-symbolic',
  'open-menu-symbolic',
  'package-x-generic-symbolic',
  'pan-down-symbolic',
  'sidebar-show-right-symbolic',
  'starred-symbolic',
  'system-search-symbolic',
  'user-bookmarks-symbolic',
  'user-trash-symbolic',
  'view-more-symbolic',
  'view-reveal-symbolic',
  'weather-clear-night-symbolic',
  'window-close-symbolic',
  'window-new-symbolic',
];

// name -> absolute path, for the icons found. Adwaita files its symbolic icons
// in context folders (actions, places, status, ui ...), so look in each.
function findIcons() {
  const found = {};
  for (const root of ROOTS) {
    let dirs;
    try {
      dirs = fs.readdirSync(root, { withFileTypes: true }).filter(d => d.isDirectory()).map(d => d.name);
    } catch (e) {
      continue;
    }
    for (const name of ICONS) {
      if (found[name]) continue;
      for (const dir of dirs) {
        const file = path.join(root, dir, `${name}.svg`);
        try {
          if (fs.statSync(file).size > 0) {
            found[name] = file;
            break;
          }
        } catch (e) {
          // not in this folder
        }
      }
    }
  }
  return found;
}

function activate() {
  const found = findIcons();
  const vars = Object.keys(found).map(name =>
    `  --adw-icon-${name}: url("file://${encodeURI(found[name])}");`);
  let style = document.getElementById(STYLE_ID);
  if (!style) {
    style = document.createElement('style');
    style.id = STYLE_ID;
    document.head.appendChild(style);
  }
  style.textContent = `:root {\n${vars.join('\n')}\n}`;
  for (const name of Object.keys(found)) document.documentElement.classList.add(`adw-icon-${name}`);
}

function deactivate() {
  const style = document.getElementById(STYLE_ID);
  if (style) style.remove();
  for (const name of ICONS) document.documentElement.classList.remove(`adw-icon-${name}`);
}

module.exports = { activate, deactivate, ICONS };

// RedFox GNOME integration for Mailspring. Adds Reply / Reply all / Forward to
// the message pane's header bar (./reply-buttons.js), and puts the window buttons where GNOME's
// "button-layout" setting says (org.gnome.desktop.wm.preferences), the way GTK
// apps do. Mailspring runs in a Flatpak, so the setting is read through the
// desktop portal (org.freedesktop.portal.Settings), and changes are followed
// live by watching the portal's SettingChanged signal.
const { execFile, spawn } = require('child_process');
const { ComponentRegistry } = require('mailspring-exports');
const RedFoxReplyButtons = require('./reply-buttons');

const STYLE_ID = 'redfox-gnome-window-buttons';
const BUTTON = 26; // a 20 px circle plus its margins, as the RedFox Adwaita theme draws them
const PORTAL = ['--session', '--dest', 'org.freedesktop.portal.Desktop', '--object-path', '/org/freedesktop/portal/desktop'];
const KNOWN = ['minimize', 'maximize', 'close'];

let monitor = null;
let lastLayout = null;

// "appmenu:minimize,maximize,close" -> { side: 'right', order: [...] }
function parseLayout(layout) {
  const [left = '', right = ''] = String(layout).split(':');
  const pick = s => s.split(',').map(t => t.trim()).filter(t => KNOWN.includes(t));
  const l = pick(left);
  const r = pick(right);
  // Mailspring keeps its buttons together, so use the side that has more of them.
  return r.length >= l.length ? { side: 'right', order: r } : { side: 'left', order: l };
}

function css({ side, order }) {
  const sel = 'body.platform-linux.redfox-gnome .toolbar-window-controls';
  const rules = [];
  if (side === 'right') {
    rules.push(`${sel} { position: fixed; top: 13px; right: 6px; left: auto; display: flex; z-index: 10; margin: 0; order: 0; width: auto; min-width: 0; }`);
    rules.push(`body.platform-linux.redfox-gnome .sheet-toolbar-container > [role='toolbar']:last-child { padding-right: ${order.length * BUTTON + 10}px; }`);
  } else {
    rules.push(`${sel} { position: static; display: flex; align-self: center; margin: 0 0 0 6px; order: -1000; width: auto; min-width: 0; }`);
    rules.push(`body.platform-linux.redfox-gnome .sheet-toolbar-container > [role='toolbar']:last-child { padding-right: 0; }`);
  }
  for (const name of KNOWN) {
    const i = order.indexOf(name);
    rules.push(i < 0
      ? `${sel} button.${name} { display: none; }`
      : `${sel} button.${name} { display: block; order: ${i + 1}; }`);
  }
  return rules.join('\n');
}

function apply(layout) {
  if (!layout || layout === lastLayout) return;
  lastLayout = layout;
  let style = document.getElementById(STYLE_ID);
  if (!style) {
    style = document.createElement('style');
    style.id = STYLE_ID;
    document.head.appendChild(style);
  }
  style.textContent = css(parseLayout(layout));
  document.body.classList.add('redfox-gnome');
}

function read() {
  // ReadOne is portal version 2; Read wraps the value one level deeper.
  const tryMethod = (method, next) => execFile('gdbus',
    ['call', ...PORTAL, '--method', `org.freedesktop.portal.Settings.${method}`,
     'org.gnome.desktop.wm.preferences', 'button-layout'],
    { timeout: 5000 }, (err, stdout) => {
      const m = !err && /'([^']*)'/.exec(stdout);
      if (m) apply(m[1]);
      else if (next) next();
    });
  tryMethod('ReadOne', () => tryMethod('Read', null));
}

function watch() {
  try {
    monitor = spawn('gdbus', ['monitor', ...PORTAL], { stdio: ['ignore', 'pipe', 'ignore'] });
    monitor.stdout.on('data', chunk => {
      if (String(chunk).includes('button-layout')) read();
    });
    monitor.on('error', () => { monitor = null; });
  } catch (e) {
    monitor = null;
  }
}

module.exports = {
  activate() {
    read();
    watch();
    ComponentRegistry.register(RedFoxReplyButtons, { role: 'ThreadActionsToolbarButton' });
  },
  deactivate() {
    ComponentRegistry.unregister(RedFoxReplyButtons);
    if (monitor) monitor.kill();
    monitor = null;
    lastLayout = null;
    const style = document.getElementById(STYLE_ID);
    if (style) style.remove();
    document.body.classList.remove('redfox-gnome');
  },
};

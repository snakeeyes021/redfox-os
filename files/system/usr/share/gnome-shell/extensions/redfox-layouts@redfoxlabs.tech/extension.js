// SPDX-License-Identifier: Apache-2.0
//
// RedFox Layouts: the parts of a RedFox layout that have to live inside
// GNOME Shell to apply without logging out. `redfox-layout` (a shell script)
// does everything else by writing settings.

import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import St from 'gi://St';

import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

const DASH_TO_DOCK = 'dash-to-dock@micxgx.gmail.com';
const TILING_SHELL = 'tilingshell@ferrarodomenico.com';

// Dash to Dock already leaves a few pixels between the dock and the screen
// edge. Floating replaces that with `gap` pixels on the screen-facing sides
// and none on the side facing the windows.
const floatingDockCss = gap => `
#dashtodockContainer #dash .dash-background { margin: 0 !important; }
#dashtodockContainer.bottom #dash { margin: 0 ${gap}px ${gap}px ${gap}px !important; }
#dashtodockContainer.top #dash { margin: ${gap}px ${gap}px 0 ${gap}px !important; }
#dashtodockContainer.left #dash { margin: ${gap}px 0 ${gap}px ${gap}px !important; }
#dashtodockContainer.right #dash { margin: ${gap}px ${gap}px ${gap}px 0 !important; }
`;

export default class RedFoxLayoutsExtension extends Extension {
    // GNOME Shell can call enable() or disable() twice in a row when the
    // enabled-extensions list changes quickly, so both are safe to repeat.
    enable() {
        if (this._settings)
            return;
        this._settings = this.getSettings();
        this._settings.connectObject(
            'changed::floating-dock', () => this._syncFloatingDock(),
            'changed::floating-dock-gap', () => this._syncFloatingDock(),
            'changed::auto-dock', () => this._queueAutoDock(),
            'changed::auto-dock-min-width', () => this._queueAutoDock(),
            'changed::tiling-button-by-start', () => this._queueTilingButton(),
            'changed::tiling-button-size', () => this._queueTilingButton(),
            this);

        // ArcMenu, Tiling Shell and Dash to Panel each rebuild their panel
        // buttons when they are turned on or off, so place the tiling button
        // again after any of them changes.
        Main.extensionManager.connectObject(
            'extension-state-changed', () => this._queueTilingButton(), this);

        // A theme change (user-theme, high contrast) builds a new St.Theme
        // and drops stylesheets loaded at runtime, so load ours into the new
        // one. 'changed' also fires when a stylesheet is (un)loaded, including
        // ours, so only act when the theme itself was replaced.
        const themeContext = St.ThemeContext.get_for_stage(global.stage);
        themeContext.connectObject('changed', () => {
            if (this._stylesheet && themeContext.get_theme() !== this._theme)
                this._syncFloatingDock();
        }, this);

        Main.layoutManager.connectObject(
            'monitors-changed', () => this._queueAutoDock(), this);

        this._syncFloatingDock();
        if (Main.layoutManager._startingUp) {
            Main.layoutManager.connectObject('startup-complete', () => {
                this._queueAutoDock();
                this._queueTilingButton();
            }, this);
        } else {
            this._queueAutoDock();
            this._queueTilingButton();
        }
    }

    disable() {
        if (!this._settings)
            return;
        Main.layoutManager.disconnectObject(this);
        Main.extensionManager.disconnectObject(this);
        St.ThemeContext.get_for_stage(global.stage).disconnectObject(this);
        this._settings.disconnectObject(this);
        this._settings = null;
        if (this._autoDockId) {
            GLib.source_remove(this._autoDockId);
            this._autoDockId = 0;
        }
        if (this._tilingButtonId) {
            GLib.source_remove(this._tilingButtonId);
            this._tilingButtonId = 0;
        }
        this._restoreTilingButton();
        this._unloadStylesheet();
    }

    _syncFloatingDock() {
        this._unloadStylesheet();
        if (!this._settings.get_boolean('floating-dock'))
            return;

        const gap = this._settings.get_int('floating-dock-gap');
        const dir = GLib.build_filenamev([GLib.get_user_runtime_dir(), this.uuid]);
        GLib.mkdir_with_parents(dir, 0o700);
        const file = Gio.File.new_for_path(GLib.build_filenamev([dir, `floating-dock-${gap}.css`]));
        file.replace_contents(new TextEncoder().encode(floatingDockCss(gap)),
            null, false, Gio.FileCreateFlags.REPLACE_DESTINATION, null);

        this._theme = St.ThemeContext.get_for_stage(global.stage).get_theme();
        this._theme.load_stylesheet(file);
        this._stylesheet = file;
    }

    // Unloads from the theme it was loaded into, which after a theme change
    // is no longer the current one (and is about to be dropped anyway).
    _unloadStylesheet() {
        if (this._stylesheet)
            this._theme?.unload_stylesheet(this._stylesheet);
        this._stylesheet = null;
        this._theme = null;
    }

    // Turning Dash to Dock on or off rewrites the enabled-extensions list,
    // which the shell handles asynchronously. Wait for things to settle
    // (a layout switch, a monitor being plugged in) before doing it.
    _queueAutoDock() {
        if (this._autoDockId)
            GLib.source_remove(this._autoDockId);
        this._autoDockId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 500, () => {
            this._autoDockId = 0;
            this._syncAutoDock();
            return GLib.SOURCE_REMOVE;
        });
    }

    // Show the dock on screens wide enough for it; leave small screens
    // (laptops) with GNOME's dash in the overview.
    _syncAutoDock() {
        if (!this._settings.get_boolean('auto-dock'))
            return;
        const monitor = Main.layoutManager.primaryMonitor;
        if (!monitor)
            return;

        const wantDock = monitor.width >= this._settings.get_int('auto-dock-min-width');
        const enabled = global.settings.get_strv('enabled-extensions').includes(DASH_TO_DOCK);
        if (wantDock && !enabled)
            Main.extensionManager.enableExtension(DASH_TO_DOCK);
        else if (!wantDock && enabled)
            Main.extensionManager.disableExtension(DASH_TO_DOCK);
    }

    _queueTilingButton() {
        if (this._tilingButtonId)
            GLib.source_remove(this._tilingButtonId);
        this._tilingButtonId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 500, () => {
            this._tilingButtonId = 0;
            this._syncTilingButton();
            return GLib.SOURCE_REMOVE;
        });
    }

    // In the Windows layouts, Tiling Shell's button sits just after the
    // start button, at app-icon size, instead of among the tray icons.
    _syncTilingButton() {
        if (!this._settings.get_boolean('tiling-button-by-start')) {
            this._restoreTilingButton();
            return;
        }

        const tiling = Main.panel.statusArea[TILING_SHELL];
        const start = Main.panel.statusArea['ArcMenu'];
        const startBox = start?.container?.get_parent();
        if (!tiling?.container || !startBox) {
            this._restoreTilingButton();
            return;
        }

        if (this._tiling !== tiling) {
            this._restoreTilingButton();
            this._tiling = tiling;
            const icon = tiling.get_first_child();
            this._tilingIcon = icon instanceof St.Icon ? icon : null;
            this._tilingIconSize = this._tilingIcon?.icon_size ?? -1;
            tiling.connectObject('destroy', () => {
                this._tiling = null;
                this._tilingIcon = null;
            }, this);
        }

        const container = tiling.container;
        if (container.get_parent() !== startBox) {
            container.get_parent()?.remove_child(container);
            startBox.insert_child_above(container, start.container);
        } else if (container.get_previous_sibling() !== start.container) {
            startBox.set_child_above_sibling(container, start.container);
        }
        if (this._tilingIcon)
            this._tilingIcon.icon_size = this._settings.get_int('tiling-button-size');
    }

    // Back among the tray icons: in the top bar's right box, just before the
    // system indicators, which is where Tiling Shell's own placement ends up.
    _restoreTilingButton() {
        const tiling = this._tiling;
        if (!tiling)
            return;
        tiling.disconnectObject(this);
        if (this._tilingIcon)
            this._tilingIcon.icon_size = this._tilingIconSize;
        const container = tiling.container;
        const box = Main.panel._rightBox;
        if (container && box && container.get_parent() !== box) {
            container.get_parent()?.remove_child(container);
            const before = ['a11y', 'keyboard', 'quickSettings']
                .map(name => Main.panel.statusArea[name]?.container)
                .find(c => c?.get_parent() === box);
            if (before)
                box.insert_child_below(container, before);
            else
                box.add_child(container);
        }
        this._tiling = null;
        this._tilingIcon = null;
    }
}

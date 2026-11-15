// SPDX-License-Identifier: Apache-2.0
//
// RedFox Layouts: the parts of a RedFox layout that have to live inside
// GNOME Shell to apply without logging out. `redfox-layout` (a shell script)
// does everything else by writing settings.

import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import St from 'gi://St';

import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import {ExtensionState} from 'resource:///org/gnome/shell/misc/extensionUtils.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

import {diagonalInches, primaryPhysicalSize, wantDock} from './autodock.js';
import {areaChanged, refitFrame} from './refit.js';

const DASH_TO_DOCK = 'dash-to-dock@micxgx.gmail.com';
const TILING_SHELL = 'tilingshell@ferrarodomenico.com';
const DASH_TO_PANEL = 'dash-to-panel@jderose9.github.com';
const DASH_TO_PANEL_SCHEMA = 'org.gnome.shell.extensions.dash-to-panel';
const TILING_SHELL_SCHEMA = 'org.gnome.shell.extensions.tilingshell';
// Tiling Shell's gaps between tiled windows and around them. They and the
// floating dock's gap are one setting: floating-dock-gap.
const TILING_GAPS = ['inner-gaps', 'outer-gaps'];
const MAX_GAP = 64;
const ACTIVE = ExtensionState.ACTIVE ?? ExtensionState.ENABLED;

/**
 * An extension's own settings, from its schemas folder or the system's.
 *
 * @param {object} extension
 * @param {string} schemaId
 * @returns {Gio.Settings|null}
 */
function extensionSettings(extension, schemaId) {
    const dir = extension.dir?.get_child('schemas');
    const parent = Gio.SettingsSchemaSource.get_default();
    let source = parent;
    if (dir?.query_exists(null))
        source = Gio.SettingsSchemaSource.new_from_directory(dir.get_path(), parent, false);
    const schema = source?.lookup(schemaId, true);
    return schema ? new Gio.Settings({settings_schema: schema}) : null;
}

// Dash to Dock already leaves a few pixels between the dock and the screen
// edge. Floating replaces that with `gap` pixels on the side facing the
// screen edge and none on the side facing the windows. The two ends along
// the dock get no margin: Dash to Dock already centres a dock that isn't
// full, and on a full one a margin there pushed the dock's end (its rounded
// background) past the space Dash to Dock gives it, where it was cut off.
//
// It's set as the dock's inline style, not a stylesheet: St keeps a stylesheet
// that has been loaded twice into one theme (GNOME copies runtime stylesheets
// into a rebuilt theme), and one unload then leaves the other in place with no
// way to remove it. The floating margins then stayed on after a switch to a
// full-height dock (RedFox -> GNOME -> Ubuntu gave it an 8 px gap).
const floatingMargins = (side, gap) => ({
    bottom: `0 0 ${gap}px 0`,
    top: `${gap}px 0 0 0`,
    left: `0 0 0 ${gap}px`,
    right: `0 ${gap}px 0 0`,
}[side]);

const DOCK_SIDES = ['bottom', 'top', 'left', 'right'];

function findByName(actor, name) {
    if (actor.name === name)
        return actor;
    for (const child of actor.get_children?.() ?? []) {
        const found = findByName(child, name);
        if (found)
            return found;
    }
    return null;
}

function findByClass(actor, styleClass) {
    if (actor.has_style_class_name?.(styleClass))
        return actor;
    for (const child of actor.get_children?.() ?? []) {
        const found = findByClass(child, styleClass);
        if (found)
            return found;
    }
    return null;
}

export default class RedFoxLayoutsExtension extends Extension {
    // GNOME Shell can call enable() or disable() twice in a row when the
    // enabled-extensions list changes quickly, so both are safe to repeat.
    enable() {
        if (this._settings)
            return;
        this._settings = this.getSettings();
        this._settings.connectObject(
            'changed::floating-dock', () => this._syncFloatingDock(),
            'changed::floating-dock-gap', () => {
                this._syncFloatingDock();
                this._syncTilingGaps();
            },
            'changed::auto-dock', () => this._queueAutoDock(),
            'changed::auto-dock-min-width', () => this._queueAutoDock(),
            'changed::auto-dock-min-inches', () => this._queueAutoDock(),
            'changed::auto-dock-small-screens', () => this._queueAutoDock(),
            'changed::tiling-button-by-start', () => this._queueTilingButton(),
            'changed::tiling-button-size', () => this._queueTilingButton(),
            this);

        // ArcMenu, Tiling Shell and Dash to Panel each rebuild their panel
        // buttons when they are turned on or off, so place the tiling button
        // again after any of them changes.
        Main.extensionManager.connectObject(
            'extension-state-changed', (_manager, extension) => {
                this._queueTilingButton();
                if (extension.uuid === DASH_TO_PANEL)
                    this._syncWorkspaceIsolation(false);
            }, this);

        // GNOME's Settings › Multitasking › App Switching choice (apps from
        // the current workspace only) also applies to the taskbar, as it does
        // to Dash to Dock: Dash to Panel only reads its own switch.
        this._appSwitcher = new Gio.Settings({schema_id: 'org.gnome.shell.app-switcher'});
        this._appSwitcher.connectObject('changed::current-workspace-only',
            () => this._syncWorkspaceIsolation(true), this);
        this._syncWorkspaceIsolation(false);

        // Tiling Shell's own gap settings (its preferences) change the one
        // gap too, which then sets the other.
        const schemas = Gio.SettingsSchemaSource.get_default();
        if (schemas?.lookup(TILING_SHELL_SCHEMA, true)) {
            this._tilingSettings = new Gio.Settings({schema_id: TILING_SHELL_SCHEMA});
            for (const key of TILING_GAPS) {
                this._tilingSettings.connectObject(`changed::${key}`,
                    () => this._tilingGapChanged(key), this);
            }
        }
        this._syncTilingGaps();

        // Tiled windows follow the tiling area when it changes (see refit.js). Tiling Shell
        // reads the new area as it's announced; look once it has.
        this._tilingAreas = new Map();
        global.display.connectObject('workareas-changed', () => this._queueRefit(), this);
        this._refitTiledWindows();

        // Dash to Dock builds its docks when it starts and when monitors or
        // its own settings change; float each new one as it appears.
        Main.uiGroup.connectObject('child-added', (_group, actor) => {
            if (actor.name === 'dashtodockContainer')
                this._watchDock(actor);
        }, this);
        this._docks = new Set();
        for (const actor of Main.uiGroup.get_children()) {
            if (actor.name === 'dashtodockContainer')
                this._watchDock(actor);
        }

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
        Main.uiGroup.disconnectObject(this);
        this._settings.disconnectObject(this);
        this._settings = null;
        this._appSwitcher.disconnectObject(this);
        this._appSwitcher = null;
        this._tilingSettings?.disconnectObject(this);
        this._tilingSettings = null;
        global.display.disconnectObject(this);
        if (this._refitId) {
            GLib.source_remove(this._refitId);
            this._refitId = 0;
        }
        this._tilingAreas = null;
        if (this._autoDockId) {
            GLib.source_remove(this._autoDockId);
            this._autoDockId = 0;
        }
        if (this._tilingButtonId) {
            GLib.source_remove(this._tilingButtonId);
            this._tilingButtonId = 0;
        }
        this._restoreTilingButton();
        for (const dock of this._docks) {
            dock.disconnectObject(this);
            this._styleDock(dock, false);
        }
        this._docks = null;
    }

    // Dash to Panel shows only the current workspace's apps while GNOME's
    // App Switching setting is "current workspace only", like Dash to Dock.
    // When that setting is turned off, Dash to Panel's switch goes off too;
    // otherwise Dash to Panel's own switch is left as it is.
    _syncWorkspaceIsolation(changed) {
        const panel = Main.extensionManager.lookup(DASH_TO_PANEL);
        if (!this._appSwitcher || panel?.state !== ACTIVE)
            return;
        const only = this._appSwitcher.get_boolean('current-workspace-only');
        if (!only && !changed)
            return;
        const settings = extensionSettings(panel, DASH_TO_PANEL_SCHEMA);
        if (settings && settings.get_boolean('isolate-workspaces') !== only)
            settings.set_boolean('isolate-workspaces', only);
    }

    _watchDock(dock) {
        if (this._docks.has(dock))
            return;
        this._docks.add(dock);
        // The side (left, bottom, ...) is a style class, which changes with
        // Dash to Dock's position setting.
        dock.connectObject(
            'notify::style-class', () => this._styleDock(dock),
            'destroy', () => this._docks?.delete(dock),
            this);
        this._styleDock(dock);
    }

    _syncFloatingDock() {
        for (const dock of this._docks ?? [])
            this._styleDock(dock);
    }

    // The gap around the floating dock is also Tiling Shell's gap between
    // tiled windows and around them, in every layout.
    _syncTilingGaps() {
        if (!this._tilingSettings)
            return;
        const gap = this._settings.get_int('floating-dock-gap');
        for (const key of TILING_GAPS) {
            if (this._tilingSettings.get_uint(key) !== gap)
                this._tilingSettings.set_uint(key, gap);
        }
    }

    _queueRefit() {
        if (this._refitId)
            return;
        this._refitId = GLib.idle_add(GLib.PRIORITY_DEFAULT_IDLE, () => {
            this._refitId = 0;
            this._refitTiledWindows();
            return GLib.SOURCE_REMOVE;
        });
    }

    // Tiling Shell's area for each monitor, as it has it now; tiled windows on a monitor whose
    // area changed since last time move into their tiles in the new area.
    _refitTiledWindows() {
        const tiling = Main.extensionManager.lookup(TILING_SHELL);
        const managers = tiling?.state === ACTIVE ? tiling.stateObj?._tilingManagers : null;
        if (!Array.isArray(managers) || !this._tilingAreas) {
            this._tilingAreas?.clear();
            return;
        }
        const changed = new Map();
        for (const manager of managers) {
            const index = manager?._monitor?.index;
            const area = manager?._workArea;
            if (index === undefined || !area)
                continue;
            const now = {x: area.x, y: area.y, width: area.width, height: area.height};
            const before = this._tilingAreas.get(index);
            this._tilingAreas.set(index, now);
            if (areaChanged(before, now))
                changed.set(index, {manager, area: now});
        }
        if (changed.size === 0)
            return;
        for (const actor of global.get_window_actors()) {
            const window = actor.meta_window;
            const monitor = changed.get(window?.get_monitor());
            const tile = window?.assignedTile;
            if (!monitor || !tile || window.fullscreen || window.maximized_horizontally ||
                window.maximized_vertically)
                continue;
            const frame = window.get_frame_rect();
            const to = refitFrame({x: frame.x, y: frame.y, width: frame.width, height: frame.height},
                tile, monitor.area, this._tilingGaps(monitor.manager, window));
            if (to)
                window.move_resize_frame(true, to.x, to.y, to.width, to.height);
        }
    }

    // The gaps Tiling Shell puts around a window in a tile on this workspace: its layout's own,
    // or failing that its settings (which the one gap keeps equal).
    _tilingGaps(manager, window) {
        const margin = m => ({top: m.top, right: m.right, bottom: m.bottom, left: m.left});
        const layout = manager._workspaceTilingLayout?.get?.(window.get_workspace());
        if (layout?.innerGaps && layout?.outerGaps)
            return {inner: margin(layout.innerGaps), outer: margin(layout.outerGaps)};
        const all = n => ({top: n, right: n, bottom: n, left: n});
        const gap = this._settings.get_int('floating-dock-gap');
        return {inner: all(gap), outer: all(gap)};
    }

    _tilingGapChanged(key) {
        const gap = Math.min(this._tilingSettings.get_uint(key), MAX_GAP);
        if (gap !== this._settings.get_int('floating-dock-gap'))
            this._settings.set_int('floating-dock-gap', gap);
        else
            this._syncTilingGaps();
    }

    // Set (or clear) the floating margins on one dock's dash and background.
    _styleDock(dock, floating = this._settings?.get_boolean('floating-dock')) {
        const dash = findByName(dock, 'dash');
        if (!dash)
            return;
        const background = findByClass(dash, 'dash-background');
        const side = DOCK_SIDES.find(s => dock.has_style_class_name(s));
        if (floating && side) {
            const gap = this._settings.get_int('floating-dock-gap');
            dash.set_style(`margin: ${floatingMargins(side, gap)};`);
            background?.set_style('margin: 0;');
        } else {
            dash.set_style(null);
            background?.set_style(null);
        }
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

    // Show the dock on big screens (by their diagonal, in inches); leave small screens
    // (smaller laptops) with GNOME's dash in the overview, unless the dock is wanted on
    // small screens too. A screen that doesn't report its size is judged by its width.
    async _syncAutoDock() {
        if (!this._settings?.get_boolean('auto-dock'))
            return;
        const monitor = Main.layoutManager.primaryMonitor;
        if (!monitor)
            return;

        let inches = null;
        try {
            const size = await this._primaryPhysicalSize();
            inches = size ? diagonalInches(size.widthMm, size.heightMm) : null;
        } catch (e) {
            inches = null;
        }
        if (!this._settings)
            return; // turned off meanwhile

        const want = wantDock({
            smallToo: this._settings.get_boolean('auto-dock-small-screens'),
            inches,
            minInches: this._settings.get_double('auto-dock-min-inches'),
            logicalWidth: monitor.width,
            minWidth: this._settings.get_int('auto-dock-min-width'),
        });
        const enabled = global.settings.get_strv('enabled-extensions').includes(DASH_TO_DOCK);
        if (want && !enabled)
            Main.extensionManager.enableExtension(DASH_TO_DOCK);
        else if (!want && enabled)
            Main.extensionManager.disableExtension(DASH_TO_DOCK);
    }

    // The primary screen's physical size, from Mutter's own display configuration.
    async _primaryPhysicalSize() {
        const call = method => new Promise((resolve, reject) => {
            Gio.DBus.session.call('org.gnome.Mutter.DisplayConfig', '/org/gnome/Mutter/DisplayConfig',
                'org.gnome.Mutter.DisplayConfig', method, null, null, Gio.DBusCallFlags.NONE, 5000,
                null, (connection, result) => {
                    try {
                        resolve(connection.call_finish(result).deepUnpack());
                    } catch (e) {
                        reject(e);
                    }
                });
        });
        const [state, resources] = await Promise.all([call('GetCurrentState'), call('GetResources')]);
        return primaryPhysicalSize(state, resources);
    }

    // ArcMenu and Tiling Shell can take a few seconds after being turned on
    // to add their buttons, so keep looking for a while if one is missing.
    _queueTilingButton(tries = 20) {
        if (this._tilingButtonId)
            GLib.source_remove(this._tilingButtonId);
        this._tilingButtonId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 500, () => {
            this._tilingButtonId = 0;
            if (!this._syncTilingButton() && tries > 1)
                this._queueTilingButton(tries - 1);
            return GLib.SOURCE_REMOVE;
        });
    }

    // In the Windows layouts, Tiling Shell's button sits just after the
    // start button, at app-icon size, instead of among the tray icons.
    // Returns false if a button it needs isn't there (yet).
    _syncTilingButton() {
        if (!this._settings.get_boolean('tiling-button-by-start')) {
            this._restoreTilingButton();
            return true;
        }

        const tiling = Main.panel.statusArea[TILING_SHELL];
        const start = Main.panel.statusArea['ArcMenu'];
        const startBox = start?.container?.get_parent();
        if (!tiling?.container || !startBox) {
            this._restoreTilingButton();
            return false;
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
        return true;
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

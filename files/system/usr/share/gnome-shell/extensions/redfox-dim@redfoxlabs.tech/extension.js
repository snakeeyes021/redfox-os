// SPDX-License-Identifier: Apache-2.0
//
// RedFox Dim: more brightness range than the backlight has. The bottom of the
// regular brightness slider holds the backlight at its minimum and darkens the
// picture instead.
//
// Everything that changes brightness (slider, keys, OSD, idle dimming, saving
// the level across logins) goes through Main.brightnessManager, and it reaches
// the hardware through one method on one class. So hooking that method extends
// all of them at once. The method is private, so if a future GNOME renames it
// the extension logs an error and stays out of the way, and the stock slider
// keeps working. tests/redfox-dim/run.sh checks all this against a real shell;
// run it when moving to a new GNOME.

import Clutter from 'gi://Clutter';
import Cogl from 'gi://Cogl';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';

import {Extension, InjectionManager} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import {QuickSlider, SystemIndicator} from 'resource:///org/gnome/shell/ui/quickSettings.js';

import {backlightFor, levelFor, valueForBacklight} from './curve.js';

const HOOKED_METHODS = ['setBacklight', '_getRelativeBrightness'];

const BRIGHTNESS_ICON = 'display-brightness-symbolic';
const SLIDER_FILL = '-st-accent-color';
const OSD_FILL = '#ffffff'; // what GNOME's light, dark and high contrast themes use
const SAVE_DELAY_MS = 300;

// GNOME's level bars can show a notch, the one where volume goes past 100%. That
// notch marks where dimming starts here too, only without the red beyond it.
function markBar(bar, position, color) {
    bar.overdriveStart = position;
    bar.style = `-barlevel-overdrive-color: ${color};`;
}

function unmarkBar(bar) {
    bar.overdriveStart = 1;
    bar.style = null;
}

// A black rectangle over one monitor. Dimming the picture on the way to the
// panel would be better still, but mutter's gamma table belongs to Night Light,
// which overwrites it whenever the color temperature changes.
const DimOverlay = GObject.registerClass(
class DimOverlay extends Clutter.Actor {
    _init() {
        super._init({reactive: false, visible: false});

        const context = global.stage.context.get_backend().get_cogl_context();
        this._pipeline = Cogl.Pipeline.new(context);
    }

    setLevel(level) {
        const color = new Cogl.Color();
        color.init_from_4f(0, 0, 0, 1 - level);
        this._pipeline.set_color(color);

        this.visible = level < 1;
        this.queue_redraw();
    }

    vfunc_get_paint_volume(volume) {
        return volume.set_from_allocation(this);
    }

    vfunc_paint(paintContext) {
        // Paint only on the way to a monitor. Screenshots paint the stage into
        // a framebuffer of their own, and should show the real picture.
        const framebuffer = paintContext.get_framebuffer();
        const onMonitor = global.stage.peek_stage_views()
            .some(view => view.get_framebuffer() === framebuffer);
        if (!onMonitor)
            return;

        const {width, height} = this;
        framebuffer.draw_rectangle(this._pipeline, 0, 0, width, height);
    }
});

// For monitors GNOME has no brightness control for, and so no slider. There's no
// backlight to move here: the whole slider dims the picture.
const FallbackSlider = GObject.registerClass(
class FallbackSlider extends QuickSlider {
    _init(position, onMoved) {
        super._init({iconName: 'weather-clear-night-symbolic'});

        this.slider.accessible_name = 'Dim monitors without brightness control';
        this.slider.value = position;
        this.slider.connect('notify::value', () => onMoved(this.slider.value));
    }
});

export default class RedFoxDimExtension extends Extension {
    enable() {
        if (this._settings)
            return;

        this._settings = this.getSettings();
        this._injections = new InjectionManager();
        this._overlays = new Map();
        this._hooked = false;
        this._slidersHooked = false;
        this._unredirectDisabled = false;
        this._uncontrolled = [];

        // The shell never calls disable() after a failed enable(), so undo
        // whatever got done here, or the hooks would outlive the extension.
        try {
            this._settings.connectObject(
                'changed::dim-range', () => this._onCurveChanged(),
                'changed::darkest-level', () => this._onCurveChanged(),
                this);
            Main.brightnessManager.connectObject('changed', () => this._onScalesChanged(), this);
            // Only there to be seen with the menu open, and at login the menu's items
            // don't exist yet when extensions start.
            Main.panel.statusArea.quickSettings.menu.connectObject('open-state-changed', (_menu, open) => {
                if (open)
                    this._onMenuOpened();
            }, this);
            Main.layoutManager.connectObject('monitors-changed', () => this._placeOverlays(), this);

            this._onScalesChanged();
        } catch (e) {
            this.disable();
            throw e;
        }
    }

    disable() {
        if (!this._settings)
            return;

        Main.brightnessManager.disconnectObject(this);
        Main.layoutManager.disconnectObject(this);
        Main.panel.statusArea.quickSettings.menu.disconnectObject(this);
        this._settings.disconnectObject(this);

        this._destroyFallbackSlider();
        this._settings = null;

        this._injections.clear();
        this._injections = null;
        if (this._hooked)
            this._unmarkBars();

        this._overlays.forEach(overlay => overlay.destroy());
        this._overlays.clear();
        this._updateUnredirect();

        // Hand the backlight back. The slider keeps its position, which now
        // means the plain backlight level again.
        if (this._hooked)
            this._reapply();
    }

    // The manager has no scales until a monitor with a backlight appears, and
    // their class isn't exported, so the first scale is how we reach it.
    _onScalesChanged() {
        const [scale] = Main.brightnessManager.scales;
        if (scale && !this._hooked)
            this._hook(Object.getPrototypeOf(scale));

        this._uncontrolled = global.backend.get_monitor_manager().get_logical_monitors()
            .filter(lm => !lm.get_monitors().some(m => m.get_backlight() && m.is_active()));
        this._syncFallbackSlider();

        const monitors = new Set([
            ...Main.brightnessManager.scales.map(s => s.monitor),
            ...this._uncontrolled,
        ]);
        for (const [monitor, overlay] of this._overlays) {
            if (!monitors.has(monitor)) {
                overlay.destroy();
                this._overlays.delete(monitor);
            }
        }
        this._placeOverlays();
        this._updateUnredirect();
    }

    _hook(scaleProto) {
        const missing = HOOKED_METHODS.filter(m => typeof scaleProto[m] !== 'function');
        if (missing.length > 0) {
            console.error(`${this.uuid}: this GNOME's brightness scale has no ` +
                `${missing.join(', ')}; not extending the brightness slider`);
            return;
        }

        const extension = this;
        this._injections.overrideMethod(scaleProto, 'setBacklight', original =>
            function (value) {
                extension._setBrightness(this, value, original);
            });
        this._injections.overrideMethod(scaleProto, '_getRelativeBrightness', original =>
            function (backlight) {
                return valueForBacklight(original.call(this, backlight), extension._range);
            });
        this._hooked = true;

        // The shell applied the saved level before extensions loaded.
        this._reapply();

        this._hookOsd();
    }

    _onCurveChanged() {
        if (this._hooked)
            this._reapply();
        this._dimUncontrolled();
        this._markSliders();
    }

    _onMenuOpened() {
        this._hookSliders();
        this._placeFallbackSlider();
    }

    // The marker is a nicety reached through more private code than the dimming,
    // so anything going wrong here costs the marker and nothing else.
    _tryMarking(what) {
        try {
            what();
        } catch (e) {
            console.error(`${this.uuid}: can't mark the brightness bars: ${e}`);
        }
    }

    get _brightnessItem() {
        return Main.panel.statusArea.quickSettings?._brightness?.quickSettingsItems[0];
    }

    _hookSliders() {
        if (!this._hooked || this._slidersHooked)
            return;

        const extension = this;
        this._tryMarking(() => {
            // Called for the main slider and each monitor's, whenever they're made.
            this._injections.overrideMethod(Object.getPrototypeOf(this._brightnessItem),
                '_connectSlider', original =>
                    function (slider, scale) {
                        original.call(this, slider, scale);
                        extension._tryMarking(() => markBar(slider, extension._range, SLIDER_FILL));
                    });
            this._slidersHooked = true;
            this._brightnessItem._sync();
        });
    }

    _hookOsd() {
        const extension = this;
        this._tryMarking(() => {
            // These windows also show volume and the like, so unmark for those.
            this._injections.overrideMethod(Main.osdWindowManager, '_showOsdWindow', original =>
                function (monitorIndex, icon, label, level, maxLevel) {
                    let bar = null;
                    extension._tryMarking(() => {
                        bar = this._osdWindows[monitorIndex]._level;
                        if (icon.to_string() === BRIGHTNESS_ICON) {
                            markBar(bar, extension._range, OSD_FILL);
                        } else {
                            unmarkBar(bar);
                            bar = null;
                        }
                    });

                    const animating = bar?.get_transition('value');
                    original.call(this, monitorIndex, icon, label, level, maxLevel);

                    // GNOME eases the bar to each new level from the start again,
                    // so while a slider is being dragged it barely moves, then
                    // jumps. Only let it ease when it has finished the last one.
                    if (animating) {
                        bar.remove_transition('value');
                        bar.value = level;
                    }
                });
        });
    }

    _markSliders() {
        if (this._slidersHooked)
            this._tryMarking(() => this._brightnessItem._sync());
    }

    _unmarkBars() {
        if (this._slidersHooked) {
            this._tryMarking(() => {
                unmarkBar(this._brightnessItem.slider);
                this._brightnessItem._sync();
            });
        }
        this._tryMarking(() => {
            Main.osdWindowManager._osdWindows.forEach(osd => unmarkBar(osd._level));
        });
    }

    _setBrightness(scale, value, setBacklight) {
        // Auto brightness steers the same value, and shouldn't take a dark room
        // as a reason to dim the picture too.
        const autoBrightness = Main.brightnessManager.autoBrightnessTarget >= 0;
        const position = autoBrightness ? Math.max(value, this._range) : value;

        setBacklight.call(scale, backlightFor(position, this._range));

        // An exception escaping into the manager would leave its update flag
        // set, and the slider dead for the rest of the session.
        try {
            this._overlayFor(scale.monitor).setLevel(levelFor(position, this._range, this._floor));
            this._updateUnredirect();
        } catch (e) {
            console.error(`${this.uuid}: can't dim: ${e}`);
        }
    }

    // Runs the manager's own update, which works out each monitor's level and
    // calls setBacklight. Its dimming setter is the public way to trigger that.
    _reapply() {
        Main.brightnessManager.dimming = Main.brightnessManager.dimming;
    }

    _syncFallbackSlider() {
        if (this._uncontrolled.length > 0 && !this._fallbackIndicator) {
            const position = this._settings.get_double('fallback-slider');
            this._fallbackItem = new FallbackSlider(position, () => {
                this._dimUncontrolled();
                this._updateUnredirect();
                this._saveFallbackSlider();
            });

            this._fallbackIndicator = new SystemIndicator();
            this._fallbackIndicator.quickSettingsItems.push(this._fallbackItem);
            Main.panel.statusArea.quickSettings.addExternalIndicator(this._fallbackIndicator, 2);
        }

        if (this._fallbackItem)
            this._fallbackItem.visible = this._uncontrolled.length > 0;

        this._dimUncontrolled();
    }

    _dimUncontrolled() {
        if (!this._fallbackItem)
            return;

        const position = this._fallbackItem.slider.value;
        const level = levelFor(position, 1, this._floor);
        // As in _setBrightness: losing the dim shouldn't cost anything else.
        try {
            this._uncontrolled.forEach(monitor => this._overlayFor(monitor).setLevel(level));
        } catch (e) {
            console.error(`${this.uuid}: can't dim: ${e}`);
        }
    }

    // Beside the regular slider, which GNOME adds after extensions start.
    _placeFallbackSlider() {
        const brightness = this._brightnessItem;
        if (!this._fallbackItem || !brightness || this._fallbackItem.get_parent() !== brightness.get_parent())
            return;
        this._tryMarking(() => brightness.get_parent().set_child_above_sibling(this._fallbackItem, brightness));
    }

    _saveFallbackSlider() {
        if (this._saveId)
            return;
        this._saveId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, SAVE_DELAY_MS, () => {
            this._saveId = 0;
            this._settings.set_double('fallback-slider', this._fallbackItem.slider.value);
            return GLib.SOURCE_REMOVE;
        });
    }

    _destroyFallbackSlider() {
        if (this._saveId) {
            GLib.source_remove(this._saveId);
            this._saveId = 0;
            this._settings.set_double('fallback-slider', this._fallbackItem.slider.value);
        }

        this._fallbackItem?.destroy();
        this._fallbackItem = null;
        this._fallbackIndicator?.destroy();
        this._fallbackIndicator = null;
        this._uncontrolled = [];
    }

    get _range() {
        return this._settings.get_double('dim-range');
    }

    get _floor() {
        return this._settings.get_double('darkest-level');
    }

    _overlayFor(monitor) {
        let overlay = this._overlays.get(monitor);
        if (!overlay) {
            overlay = new DimOverlay();
            // On the stage rather than in uiGroup, so it stays above everything
            // the shell draws, the lock screen included, and the magnifier
            // doesn't scale it.
            global.stage.add_child(overlay);
            this._overlays.set(monitor, overlay);
            this._placeOverlay(monitor, overlay);
        }
        return overlay;
    }

    _placeOverlays() {
        this._overlays.forEach((overlay, monitor) => this._placeOverlay(monitor, overlay));
    }

    _placeOverlay(monitor, overlay) {
        const geometry = Main.layoutManager.monitors[monitor.get_number()];
        if (geometry)
            overlay.set({x: geometry.x, y: geometry.y, width: geometry.width, height: geometry.height});
    }

    // A fullscreen window scanned out directly to the panel would skip the
    // compositor, and so the overlay.
    _updateUnredirect() {
        const dimmed = [...this._overlays.values()].some(o => o.visible);
        if (dimmed === this._unredirectDisabled)
            return;

        if (dimmed)
            global.compositor.disable_unredirect();
        else
            global.compositor.enable_unredirect();
        this._unredirectDisabled = dimmed;
    }
}

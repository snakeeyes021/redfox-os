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
import GObject from 'gi://GObject';

import {Extension, InjectionManager} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

import {backlightFor, levelFor, valueForBacklight} from './curve.js';

const HOOKED_METHODS = ['setBacklight', '_getRelativeBrightness'];

const BRIGHTNESS_ICON = 'display-brightness-symbolic';
const SLIDER_FILL = '-st-accent-color';
const OSD_FILL = '#ffffff'; // what GNOME's light, dark and high contrast themes use

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

export default class RedFoxDimExtension extends Extension {
    enable() {
        if (this._settings)
            return;

        this._settings = this.getSettings();
        this._injections = new InjectionManager();
        this._overlays = new Map();
        this._hooked = false;
        this._unredirectDisabled = false;

        this._settings.connectObject('changed', () => {
            this._reapply();
            this._markSliders();
        }, this);
        Main.brightnessManager.connectObject('changed', () => this._onScalesChanged(), this);
        Main.layoutManager.connectObject('monitors-changed', () => this._placeOverlays(), this);

        this._onScalesChanged();
    }

    disable() {
        if (!this._settings)
            return;

        Main.brightnessManager.disconnectObject(this);
        Main.layoutManager.disconnectObject(this);
        this._settings.disconnectObject(this);
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

        const monitors = new Set(Main.brightnessManager.scales.map(s => s.monitor));
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

        this._hookBars();
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

    _hookBars() {
        const extension = this;

        this._tryMarking(() => {
            // Called for the main slider and each monitor's, whenever they're made.
            this._injections.overrideMethod(Object.getPrototypeOf(this._brightnessItem),
                '_connectSlider', original =>
                    function (slider, scale) {
                        original.call(this, slider, scale);
                        extension._tryMarking(() => markBar(slider, extension._range, SLIDER_FILL));
                    });
            this._markSliders();
        });

        this._tryMarking(() => {
            // These windows also show volume and the like, so unmark for those.
            this._injections.overrideMethod(Main.osdWindowManager, '_showOsdWindow', original =>
                function (monitorIndex, icon, ...rest) {
                    extension._tryMarking(() => {
                        const bar = this._osdWindows[monitorIndex]._level;
                        if (icon.to_string() === BRIGHTNESS_ICON)
                            markBar(bar, extension._range, OSD_FILL);
                        else
                            unmarkBar(bar);
                    });
                    original.call(this, monitorIndex, icon, ...rest);
                });
        });
    }

    _markSliders() {
        if (this._hooked)
            this._tryMarking(() => this._brightnessItem._sync());
    }

    _unmarkBars() {
        this._tryMarking(() => {
            unmarkBar(this._brightnessItem.slider);
            this._brightnessItem._sync();
        });
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

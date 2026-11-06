// SPDX-License-Identifier: Apache-2.0
//
// Runs inside a throwaway headless GNOME Shell (see run.sh). A headless shell's
// virtual monitor has no backlight, so this gives it a pretend one and then
// drives the shell's own BrightnessManager, slider and key handlers.

import Clutter from 'gi://Clutter';
import Cogl from 'gi://Cogl';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import Meta from 'gi://Meta';
import Shell from 'gi://Shell';
import St from 'gi://St';

import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

const UUID = 'redfox-dim@redfoxlabs.tech';
const ACTIVE = 1; // ExtensionState.ACTIVE
const MIN = 1920;
const MAX = 192000;
const near = (a, b, tolerance = 0.002) => Math.abs(a - b) <= tolerance;
const sleep = ms => new Promise(resolve => GLib.timeout_add(GLib.PRIORITY_DEFAULT, ms, () => {
    resolve();
    return GLib.SOURCE_REMOVE;
}));

const orTimeout = (promise, what) => Promise.race([
    promise,
    sleep(5000).then(() => {
        throw new Error(`${what} timed out`);
    }),
]);

const FakeBacklight = GObject.registerClass({
    Properties: {
        'brightness': GObject.ParamSpec.int('brightness', null, null,
            GObject.ParamFlags.READWRITE, 0, MAX, MAX),
    },
}, class FakeBacklight extends GObject.Object {
    _brightness = MAX;

    get brightness() {
        return this._brightness;
    }

    // Notifies only on a change, like the real one. A notify from inside a notify
    // restarts the first, so always notifying here never ends.
    set brightness(value) {
        const brightness = Math.round(value);
        if (brightness === this._brightness)
            return;
        this._brightness = brightness;
        this.notify('brightness');
    }

    get brightnessMin() {
        return MIN;
    }

    get brightnessMax() {
        return MAX;
    }

    get relative() {
        return (this._brightness - MIN) / (MAX - MIN);
    }
});

export default class DriverExtension extends Extension {
    enable() {
        this._results = [];
        this._run()
            .catch(e => this._check(`no exception: ${e}\n${e.stack}`, false))
            .finally(() => this._finish());
    }

    disable() {
    }

    _check(name, ok, detail = '') {
        this._results.push({name, ok: !!ok, detail: `${detail}`});
        this._save(); // so a hang still shows how far it got
    }

    _save() {
        const path = GLib.getenv('REDFOX_DIM_TEST_RESULT');
        GLib.file_set_contents(path, JSON.stringify(this._results, null, 1));
    }

    _finish() {
        this._check('finished', true);
        global.context.terminate();
    }

    get _dim() {
        return Main.extensionManager.lookup(UUID);
    }

    get _ext() {
        return this._dim?.stateObj;
    }

    get _overlays() {
        return [...this._ext._overlays.values()];
    }

    async _setEnabled(enabled) {
        if (enabled)
            Main.extensionManager.enableExtension(UUID);
        else
            Main.extensionManager.disableExtension(UUID);
        for (let i = 0; i < 100 && (this._dim?.state === ACTIVE) !== enabled; i++)
            await sleep(20);
    }

    _installBacklight() {
        this._backlight = new FakeBacklight();
        Meta.Monitor.prototype.get_backlight = () => this._backlight;
        Main.brightnessManager._monitorsChanged();
    }

    async _asIfOnMonitor(callback) {
        const PaintContext = Clutter.PaintContext.prototype;
        const getFramebuffer = PaintContext.get_framebuffer;
        const peekStageViews = global.stage.peek_stage_views;
        let current;
        PaintContext.get_framebuffer = function () {
            current = getFramebuffer.call(this);
            return current;
        };
        global.stage.peek_stage_views = () => [{get_framebuffer: () => current}];
        try {
            return await callback();
        } finally {
            PaintContext.get_framebuffer = getFramebuffer;
            delete global.stage.peek_stage_views;
            if (global.stage.peek_stage_views !== peekStageViews)
                global.stage.peek_stage_views = peekStageViews;
        }
    }

    async _screenshotPixel(x, y) {
        await sleep(50);
        const stream = Gio.MemoryOutputStream.new_resizable();
        await orTimeout(new Shell.Screenshot().screenshot(false, stream), 'screenshot');
        stream.close(null);
        const {default: GdkPixbuf} = await import('gi://GdkPixbuf');
        const pixbuf = GdkPixbuf.Pixbuf.new_from_stream(
            Gio.MemoryInputStream.new_from_bytes(stream.steal_as_bytes()), null);
        const offset = y * pixbuf.rowstride + x * pixbuf.n_channels;
        return pixbuf.get_pixels()[offset];
    }

    async _run() {
        Gio._promisify(Shell.Screenshot.prototype, 'screenshot');

        await sleep(500);
        const phase = GLib.getenv('REDFOX_DIM_TEST_PHASE');
        const manager = Main.brightnessManager;

        this._installBacklight();
        const scale = () => manager.globalScale;
        this._check('a backlit monitor gives the manager a scale', manager.scales.length === 1);

        await this._setEnabled(true);
        this._check('extension is active', this._dim?.state === ACTIVE, this._dim?.error);
        this._check('hooks installed', this._ext._hooked);

        if (phase === 'restart') {
            await this._afterRestart(manager);
            return;
        }

        scale().value = 1;
        this._check('top of slider: backlight at maximum', this._backlight.brightness === MAX);
        this._check('top of slider: nothing dimmed',
            this._overlays.every(o => !o.visible));

        scale().value = 0.5;
        this._check('middle of slider: backlight stretched over the rest',
            near(this._backlight.relative, 1 / 3), this._backlight.relative);
        this._check('middle of slider: nothing dimmed', this._overlays.every(o => !o.visible));

        scale().value = 0.25;
        this._check('edge of the dim range: backlight at minimum', this._backlight.brightness === MIN);
        this._check('edge of the dim range: nothing dimmed', this._overlays.every(o => !o.visible));

        scale().value = 0.1;
        this._check('dim range: backlight at minimum', this._backlight.brightness === MIN);
        this._check('dim range: one overlay showing',
            this._overlays.length === 1 && this._overlays[0].visible);
        this._check('dim range: direct scanout inhibited', this._ext._unredirectDisabled);

        const [overlay] = this._overlays;
        const [monitor] = Main.layoutManager.monitors;
        this._check('overlay covers the monitor',
            overlay.x === monitor.x && overlay.y === monitor.y &&
            overlay.width === monitor.width && overlay.height === monitor.height,
            `${overlay.x},${overlay.y} ${overlay.width}x${overlay.height}`);
        this._check('overlay is the top stage child',
            global.stage.get_last_child() === overlay);

        // What actually reaches the monitor, against what a screenshot records.
        const white = new St.Widget({
            style: 'background-color: white',
            x: monitor.x, y: monitor.y, width: monitor.width, height: monitor.height,
        });
        Main.layoutManager.uiGroup.add_child(white);
        const x = 100, y = 100;

        // A real frame draws the overlay onto the monitor's own framebuffer.
        const drawn = [];
        const FB = Cogl.Framebuffer.prototype;
        const drawRectangle = FB.draw_rectangle;
        FB.draw_rectangle = function (...args) {
            drawn.push(this);
            return drawRectangle.apply(this, args);
        };
        global.stage.queue_redraw();
        await sleep(200);
        FB.draw_rectangle = drawRectangle;
        const viewFramebuffers = global.stage.peek_stage_views().map(v => v.get_framebuffer());
        this._check('dim range: a frame draws the overlay on the monitor',
            drawn.length > 0 && drawn.every(fb => viewFramebuffers.includes(fb)), drawn.length);

        const shot = await this._screenshotPixel(x, y);
        this._check('dim range: screenshots show the undimmed picture', shot > 245, `pixel ${shot}`);

        // JS can't read a monitor's framebuffer back, but a screenshot that the
        // overlay takes for a monitor shows what it does to the pixels.
        const pixelOnMonitor = await this._asIfOnMonitor(() => this._screenshotPixel(x, y));
        const expected = 255 * (0.2 + 0.8 * (0.1 / 0.25));
        this._check('dim range: the overlay darkens by the right amount',
            Math.abs(pixelOnMonitor - expected) < 8, `pixel ${pixelOnMonitor}, expected about ${expected}`);

        const hit = global.stage.get_actor_at_pos(Clutter.PickMode.REACTIVE, x, y);
        this._check('overlay never takes input', hit !== overlay, `${hit}`);

        scale().value = 0;
        const darkest = await this._asIfOnMonitor(() => this._screenshotPixel(x, y));
        this._check('bottom of slider: darkest level, not black',
            Math.abs(darkest - 255 * 0.2) < 8, `pixel ${darkest}`);

        scale().value = 1;
        const undimmed = await this._asIfOnMonitor(() => this._screenshotPixel(x, y));
        this._check('top of slider: monitor shows the full picture', undimmed > 245, `pixel ${undimmed}`);
        this._check('undimmed: direct scanout allowed again', !this._ext._unredirectDisabled);
        white.destroy();

        // The other ways brightness changes.
        const qs = Main.panel.statusArea.quickSettings._brightness.quickSettingsItems[0];
        scale().value = 0.1;
        this._check('quick settings slider follows the value', near(qs.slider.value, 0.1), qs.slider.value);
        qs.slider.value = 0.05;
        this._check('quick settings slider drives the value', near(scale().value, 0.05), scale().value);
        this._check('quick settings slider reaches the overlay',
            near(overlay._pipeline.get_color().alpha / 255, 1 - (0.2 + 0.8 * 0.2), 0.01),
            overlay._pipeline.get_color().alpha);

        scale().value = 0.3;
        for (let i = 0; i < 2; i++)
            manager._screenBrightnessDown();
        this._check('brightness keys step into the dim range',
            near(scale().value, 0.2) && overlay.visible, scale().value);
        manager._screenBrightnessUp();
        manager._screenBrightnessUp();
        this._check('brightness keys step back out of it',
            near(scale().value, 0.3) && !overlay.visible, scale().value);
        this._check('OSD shown for key presses',
            Main.osdWindowManager._osdWindows.some(w => w.visible));

        scale().value = 0.8;
        manager.dimming = true;
        this._check('idle dim clips to its target',
            near(this._backlight.relative, (0.3 - 0.25) / 0.75), this._backlight.relative);
        manager.dimming = false;
        this._check('idle dim ends at the old level',
            near(this._backlight.relative, (0.8 - 0.25) / 0.75), this._backlight.relative);

        scale().value = 0.1;
        manager.autoBrightnessTarget = 0.0;
        this._check('auto brightness never dims the picture', !overlay.visible);
        this._check('auto brightness: backlight at minimum', this._backlight.brightness === MIN);
        manager.autoBrightnessTarget = -1.0;
        this._check('dim comes back with auto brightness off', overlay.visible);

        scale().value = 0.1;
        this._backlight.brightness = MIN + 0.5 * (MAX - MIN);
        await sleep(20);
        this._check('backlight changed elsewhere moves the slider',
            near(manager.scales[0].value, 0.625), manager.scales[0].value);
        this._check('backlight changed elsewhere ends the dim', !overlay.visible);

        const settings = this._ext._settings;
        scale().value = 0;
        settings.set_double('darkest-level', 0.5);
        await sleep(20);
        this._check('darkest-level applies right away',
            near(overlay._pipeline.get_color().alpha / 255, 0.5, 0.01), overlay._pipeline.get_color().alpha);
        settings.reset('darkest-level');
        settings.set_double('dim-range', 0.5);
        scale().value = 0.5;
        await sleep(20);
        this._check('dim-range applies right away', !overlay.visible && this._backlight.brightness === MIN);
        settings.reset('dim-range');

        // Monitors reconfigure, for example on resume or hotplug.
        scale().value = 0.1;
        const gone = this._ext._overlayFor({get_number: () => 0});
        gone.setLevel(0.5);
        this._check('monitor change: a second monitor gets its own overlay', this._overlays.length === 2);
        manager._monitorsChanged();
        await sleep(20);
        this._check('monitor change: the overlay of a monitor that left is removed',
            this._overlays.length === 1 && this._overlays[0].visible &&
            !global.stage.get_children().includes(gone), this._overlays.length);

        // Lock screen
        scale().value = 0.1;
        Main.sessionMode.pushMode('unlock-dialog');
        await sleep(100);
        this._check('stays on over the lock screen',
            this._dim.state === ACTIVE && this._overlays[0].visible);
        Main.sessionMode.popMode('unlock-dialog');
        await sleep(100);

        // Leaves the level saved for phase two
        scale().value = 0.1;
        await sleep(500);

        // Off and on again, twice
        for (let i = 0; i < 2; i++) {
            await this._setEnabled(false);
            const stage = global.stage.get_children().filter(a => a.constructor.name.includes('DimOverlay'));
            this._check(`disabled (${i}): no overlays on the stage`, stage.length === 0, stage.length);
            this._check(`disabled (${i}): the value is the plain backlight again`,
                near(this._backlight.relative, manager.scales[0].value), this._backlight.relative);
            manager.scales[0].value = 0.6;
            this._check(`disabled (${i}): stock slider works`,
                near(this._backlight.relative, 0.6), this._backlight.relative);

            manager.scales[0].value = 0.1;
            await this._setEnabled(true);
            this._check(`enabled again (${i}): dimmed`,
                this._overlays.length === 1 && this._overlays[0].visible &&
                this._backlight.brightness === MIN);
        }
        await sleep(500);

        await this._failsSoftly(manager);
    }

    // What a future GNOME might do to us
    async _failsSoftly(manager) {
        const proto = Object.getPrototypeOf(manager.scales[0]);

        await this._setEnabled(false);
        const setBacklight = proto.setBacklight;
        delete proto.setBacklight;
        await this._setEnabled(true);
        this._check('hooked method gone: still active, not hooked',
            this._dim.state === ACTIVE && !this._ext._hooked, this._dim.error);
        await this._setEnabled(false);
        proto.setBacklight = setBacklight;
        manager.scales[0].value = 0.6;
        this._check('hooked method gone: nothing left behind', near(this._backlight.relative, 0.6));

        await this._setEnabled(true);
        this._ext._overlayFor = () => {
            throw new Error('expected by the test');
        };
        manager.globalScale.value = 0.75;
        this._check('overlay failing: slider still drives the backlight',
            near(this._backlight.relative, 2 / 3), this._backlight.relative);
        this._check('overlay failing: slider keeps responding', !manager._inhibitUpdates);
        manager.globalScale.value = 1;
        this._check('overlay failing: and again', this._backlight.brightness === MAX);
        await this._setEnabled(false);
    }

    async _afterRestart(manager) {
        this._check('restart: the slider position came back',
            near(manager.scales[0].value, 0.1), manager.scales[0].value);
        this._check('restart: backlight at minimum', this._backlight.brightness === MIN,
            this._backlight.brightness);
        this._check('restart: picture dimmed',
            this._overlays.length === 1 && this._overlays[0].visible);
    }
}

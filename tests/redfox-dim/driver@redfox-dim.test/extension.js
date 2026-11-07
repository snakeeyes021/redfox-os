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
        // Disabling an extension restarts the ones loaded after it, maybe this one
        if (this._results)
            return;

        this._results = [];
        // Before redfox-dim starts, if it's in the same login as us
        if (GLib.getenv('REDFOX_DIM_TEST_PHASE') === 'startup')
            this._installBacklight();
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

    _installBacklight(connector = null) {
        const backlight = new FakeBacklight();
        this._backlight = backlight;
        Meta.Monitor.prototype.get_backlight = function () {
            return !connector || this.get_connector() === connector ? backlight : null;
        };
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

        if (phase === 'startup') {
            await this._afterLogin(manager);
            return;
        }
        if (phase === 'no-backlight') {
            await this._noBacklight();
            return;
        }
        if (phase === 'mixed') {
            await this._mixed(manager);
            return;
        }

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
        await this._checkMarkers(qs, 0.25);
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

        const lag = await this._osdLagDuringDrag(manager);
        this._check('dragging: the OSD keeps up', lag < 0.05, lag);

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

        settings.set_double('dim-range', 0.4);
        await sleep(20);
        this._check('dim-range moves the marker', near(qs.slider.overdriveStart, 0.4), qs.slider.overdriveStart);
        settings.reset('dim-range');
        await sleep(20);

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
            this._check(`disabled (${i}): no markers left`,
                qs.slider.overdriveStart === 1 && qs.slider.style === null &&
                this._monitorSliders(qs).every(b => b.overdriveStart === 1 && b.style === null) &&
                Main.osdWindowManager._osdWindows.every(w => w._level.overdriveStart === 1 && w._level.style === null));
            this._check(`disabled (${i}): stock slider works`,
                near(this._backlight.relative, 0.6), this._backlight.relative);

            manager.scales[0].value = 0.1;
            await this._setEnabled(true);
            this._openMenu();
            this._check(`enabled again (${i}): marked`, near(qs.slider.overdriveStart, 0.25));
            this._closeMenu();
            this._check(`enabled again (${i}): dimmed`,
                this._overlays.length === 1 && this._overlays[0].visible &&
                this._backlight.brightness === MIN);
        }
        await sleep(500);

        await this._failsSoftly(manager);
    }

    _monitorSliders(item) {
        const found = [];
        const walk = actor => {
            if (actor.has_style_class_name?.('slider'))
                found.push(actor);
            actor.get_children?.().forEach(walk);
        };
        walk(item._monitorBrightnessSection.actor);
        return found;
    }

    async _checkMarkers(qs, position) {
        const sameFill = bar => {
            const node = bar.get_theme_node();
            return node.get_color('-barlevel-overdrive-color')
                .equal(node.get_color('-barlevel-active-background-color'));
        };

        this._openMenu();
        this._check('marker: on the main slider', near(qs.slider.overdriveStart, position), qs.slider.overdriveStart);
        this._check('marker: no red past it on the slider', sameFill(qs.slider));
        const sliders = this._monitorSliders(qs);
        this._check('marker: on the per-monitor slider',
            sliders.length === 1 && near(sliders[0].overdriveStart, position), sliders.length);

        const {_osdWindows: [osd]} = Main.osdWindowManager;
        Main.brightnessManager._screenBrightnessDown();
        this._check('marker: on the brightness OSD', near(osd._level.overdriveStart, position), osd._level.overdriveStart);
        this._check('marker: no red past it on the OSD', sameFill(osd._level));

        Main.osdWindowManager.show(Gio.Icon.new_for_string('audio-volume-high-symbolic'),
            null, {0: {level: 1.2, maxLevel: 1.5}});
        this._check('marker: not on the volume OSD, which stays stock',
            osd._level.overdriveStart === 1 && osd._level.style === null, osd._level.overdriveStart);
        Main.brightnessManager._screenBrightnessUp();
        this._check('marker: back on the next brightness OSD', near(osd._level.overdriveStart, position));
        this._closeMenu();
    }

    _openMenu() {
        Main.panel.statusArea.quickSettings.menu.open(false);
    }

    _closeMenu() {
        Main.panel.statusArea.quickSettings.menu.close(false);
    }

    // How far the on-screen bar falls behind while a slider is dragged at a frame
    // per step. GNOME's own easing lets it stall, then jump.
    async _osdLagDuringDrag(manager) {
        const {_osdWindows: [osd]} = Main.osdWindowManager;
        manager.globalScale.value = 0;
        await sleep(150);

        let worst = 0;
        for (let i = 1; i <= 60; i++) {
            manager.globalScale.value = i / 60;
            await sleep(16);
            worst = Math.max(worst, Math.abs(osd._level.value - i / 60));
        }
        return worst;
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

        // The marker's private paths going away
        const quickSettings = Main.panel.statusArea.quickSettings;
        const brightness = quickSettings._brightness;
        quickSettings._brightness = null;
        manager.scales[0].value = 0.1;
        await this._setEnabled(true);
        this._check('no quick settings item to mark: still dims',
            this._dim.state === ACTIVE && this._ext._hooked && this._overlays[0].visible, this._dim.error);

        const {_osdWindows: [osd]} = Main.osdWindowManager;
        Object.defineProperty(osd._level, 'overdriveStart', {
            configurable: true,
            set() {
                throw new Error('expected by the test');
            },
        });
        manager._screenBrightnessUp();
        delete osd._level.overdriveStart;
        this._check('OSD bar can\'t be marked: the key press still works',
            near(manager.scales[0].value, 0.15) && !manager._inhibitUpdates, manager.scales[0].value);

        this._openMenu();
        this._closeMenu();
        this._check('menu opened with no item to mark: still dims', this._overlays[0].visible);

        // Which is how every login starts: the item arrives after the extension
        quickSettings._brightness = brightness;
        this._openMenu();
        this._check('item arrives after the extension: marked when the menu opens',
            near(brightness.quickSettingsItems[0].slider.overdriveStart, 0.25));
        this._closeMenu();
        await this._setEnabled(false);

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

    // Started along with the shell, as at a real login
    async _afterLogin(manager) {
        for (let i = 0; i < 100 && this._dim?.state !== ACTIVE; i++)
            await sleep(20);
        this._check('login: extension is active', this._dim?.state === ACTIVE, this._dim?.error);
        await sleep(500);

        const item = Main.panel.statusArea.quickSettings._brightness.quickSettingsItems[0];
        this._openMenu();
        this._check('login: the slider is marked when the menu opens',
            near(item.slider.overdriveStart, 0.25), item.slider.overdriveStart);
        this._closeMenu();

        manager.globalScale.value = 0.5;
        this._check('login: the slider drives the backlight', near(this._backlight.relative, 1 / 3));
        await this._setEnabled(false);
    }

    _alpha(overlay) {
        return overlay._pipeline.get_color().alpha / 255;
    }

    async _noBacklight() {
        const quickSettings = Main.panel.statusArea.quickSettings;
        const stock = quickSettings._brightness.quickSettingsItems[0];
        await this._setEnabled(true);

        this._check('no backlight: GNOME has no slider', !stock.visible && !Main.brightnessManager.globalScale);
        const item = this._ext._fallbackItem;
        this._check('no backlight: the fallback slider shows', item?.visible);
        this._check('no backlight: nothing hooked', !this._ext._hooked);
        this._check('no backlight: undimmed to start', this._overlays.every(o => !o.visible));

        item.slider.value = 0;
        this._check('no backlight: slider at 0 is the darkest level',
            this._overlays.length === 1 && this._overlays[0].visible && near(this._alpha(this._overlays[0]), 0.8, 0.01),
            this._overlays.length);
        this._check('no backlight: direct scanout inhibited', this._ext._unredirectDisabled);
        item.slider.value = 0.5;
        this._check('no backlight: slider in the middle', near(this._alpha(this._overlays[0]), 0.4, 0.01));
        this._ext._settings.set_double('darkest-level', 0.5);
        await sleep(20);
        this._check('no backlight: darkest-level applies right away', near(this._alpha(this._overlays[0]), 0.25, 0.01));
        this._ext._settings.reset('darkest-level');
        await sleep(20);

        this._openMenu();
        this._closeMenu();
        item.slider.value = 1;
        this._check('no backlight: slider at 1 is undimmed',
            this._overlays.every(o => !o.visible) && !this._ext._unredirectDisabled);

        item.slider.value = 0.3;
        const ext = this._ext;
        await this._setEnabled(false); // before the delayed save
        this._check('no backlight: disabled, overlay gone',
            !global.stage.get_children().some(a => a.constructor.name.includes('DimOverlay')));
        this._check('no backlight: disabled, scanout allowed', !ext._unredirectDisabled);
        this._check('no backlight: disabled, slider gone', !item.get_parent?.());

        await this._setEnabled(true);
        this._check('no backlight: position comes back',
            near(this._ext._fallbackItem.slider.value, 0.3) && this._overlays[0].visible,
            this._ext._fallbackItem.slider.value);
        this._ext._fallbackItem.slider.value = 1;
        await sleep(400);
        await this._setEnabled(false);
    }

    // A laptop panel beside a monitor with no brightness control
    async _mixed(manager) {
        this._installBacklight('Meta-0');
        await this._setEnabled(true);

        const ext = this._ext;
        const item = ext._fallbackItem;
        const stock = Main.panel.statusArea.quickSettings._brightness.quickSettingsItems[0];
        this._check('mixed: two monitors', Main.layoutManager.monitors.length === 2, Main.layoutManager.monitors.length);
        this._check('mixed: GNOME\'s slider for the panel', stock.visible && manager.scales.length === 1);
        this._check('mixed: and the fallback slider for the other', item?.visible);

        this._openMenu();
        this._check('mixed: the fallback slider sits right after GNOME\'s',
            stock.get_next_sibling() === item, stock.get_next_sibling());
        this._closeMenu();

        const overlay = monitor => ext._overlays.get(monitor);
        const panel = manager.scales[0].monitor;
        const [other] = ext._uncontrolled;
        this._check('mixed: one monitor each', ext._uncontrolled.length === 1 && other !== panel);

        manager.globalScale.value = 0.1;
        item.slider.value = 1;
        this._check('mixed: GNOME\'s slider dims only the panel',
            overlay(panel).visible && !overlay(other).visible && this._backlight.brightness === MIN);
        manager.globalScale.value = 1;
        item.slider.value = 0;
        this._check('mixed: the fallback slider dims only the other',
            !overlay(panel).visible && overlay(other).visible && this._backlight.brightness === MAX);
        this._check('mixed: on the monitor it belongs to',
            overlay(other).x === Main.layoutManager.monitors[other.get_number()].x);

        manager._monitorsChanged();
        await sleep(20);
        this._check('mixed: a monitor change keeps both', ext._overlays.size === 2 && overlay(other).visible);

        // The other monitor gains a brightness control, or leaves
        Meta.Monitor.prototype.get_backlight = () => this._backlight;
        manager._monitorsChanged();
        await sleep(20);
        this._check('mixed: every monitor controlled, the fallback slider hides',
            !item.visible && !overlay(other)?.visible);

        item.slider.value = 1;
        await sleep(400);
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

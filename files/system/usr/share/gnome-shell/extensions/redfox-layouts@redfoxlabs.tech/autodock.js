// SPDX-License-Identifier: Apache-2.0
//
// Which screens get the dock in the RedFox layout: the screen's diagonal in inches against the
// user's threshold, or always when the dock is wanted on small screens too. Screens that don't
// report their size use their width in logical pixels instead. Kept apart from extension.js so
// it can be tested outside GNOME Shell.

const MM_PER_INCH = 25.4;
// Sizes some screens report that are really their aspect ratio (the ones Mutter also ignores).
const ASPECT_AS_SIZE = [[16, 9], [16, 10], [160, 90], [160, 100], [1600, 900], [1600, 1000]];

/**
 * The diagonal in inches, or null when the screen doesn't report a real size (some report
 * nothing, some only their aspect ratio, such as 16 by 9 "millimetres").
 *
 * @param {number} widthMm
 * @param {number} heightMm
 * @returns {number|null}
 */
export function diagonalInches(widthMm, heightMm) {
    if (!(widthMm > 0 && heightMm > 0))
        return null;
    if (widthMm < 100 && heightMm < 100)
        return null;
    if (ASPECT_AS_SIZE.some(([w, h]) => widthMm === w && heightMm === h))
        return null;
    return Math.hypot(widthMm, heightMm) / MM_PER_INCH;
}

/**
 * Whether the primary screen gets the dock.
 *
 * @param {object} args
 * @param {boolean} args.smallToo - the dock on small screens too
 * @param {number|null} args.inches - the screen's diagonal, or null if unknown
 * @param {number} args.minInches - the smallest diagonal that gets the dock
 * @param {number} args.logicalWidth - the screen's width in logical pixels
 * @param {number} args.minWidth - the smallest width that gets the dock, when the size is unknown
 * @returns {boolean}
 */
export function wantDock({smallToo, inches, minInches, logicalWidth, minWidth}) {
    if (smallToo)
        return true;
    if (inches !== null && inches !== undefined)
        return inches >= minInches;
    return logicalWidth >= minWidth;
}

/**
 * The primary screen's physical size from Mutter's DisplayConfig answers (unpacked with
 * deepUnpack): GetCurrentState says which connector is primary, GetResources has each
 * output's width-mm and height-mm. Null if it can't be told.
 *
 * @param {Array} state - GetCurrentState's (serial, monitors, logical monitors, properties)
 * @param {Array} resources - GetResources's (serial, crtcs, outputs, modes, max width, max height)
 * @returns {{widthMm: number, heightMm: number}|null}
 */
export function primaryPhysicalSize(state, resources) {
    const logicalMonitors = state?.[2] ?? [];
    const primary = logicalMonitors.find(lm => lm[4]);
    const connector = primary?.[5]?.[0]?.[0];
    if (!connector)
        return null;
    const output = (resources?.[2] ?? []).find(o => o[4] === connector);
    const props = output?.[7] ?? {};
    const value = v => (v && typeof v.unpack === 'function' ? v.unpack() : v);
    const widthMm = Number(value(props['width-mm']));
    const heightMm = Number(value(props['height-mm']));
    if (!(widthMm > 0 && heightMm > 0))
        return null;
    return {widthMm, heightMm};
}

// SPDX-License-Identifier: Apache-2.0
//
// Tiled windows follow the tiling area. Tiling Shell works its tiles out from the work area
// (the screen less the top bar and the dock), and when that changes (the dock turned off or
// on, the screen resized) it lays its tiles out again, but windows already in a tile stay where
// they were: with the dock gone, they keep clear of where it was. These work out where such a
// window goes instead, the way Tiling Shell places a window in a tile: the tile in the area,
// less a gap on each side (the outer gap at the area's edges, half the inner gap between
// tiles). Kept apart from extension.js so it can be tested outside GNOME Shell.

/**
 * A tile (fractions of the area, as Tiling Shell keeps it on the window) in an area, in pixels,
 * rounded and cut back to the area as Tiling Shell does it.
 *
 * @param {{x: number, y: number, width: number, height: number}} tile
 * @param {{x: number, y: number, width: number, height: number}} area
 * @returns {{x: number, y: number, width: number, height: number}}
 */
export function tileRect(tile, area) {
    const rect = {
        x: Math.round(area.width * tile.x + area.x),
        y: Math.round(area.height * tile.y + area.y),
        width: Math.round(area.width * tile.width),
        height: Math.round(area.height * tile.height),
    };
    rect.width = Math.min(rect.width, area.x + area.width - rect.x);
    rect.height = Math.min(rect.height, area.y + area.height - rect.y);
    return rect;
}

/**
 * Where a window in this tile goes in this area: the tile less its gaps.
 *
 * @param {{x: number, y: number, width: number, height: number}} tile
 * @param {{x: number, y: number, width: number, height: number}} area
 * @param {{inner: object, outer: object}} gaps - each {top, right, bottom, left}, in pixels
 * @returns {{x: number, y: number, width: number, height: number}|null}
 */
export function tiledFrame(tile, area, gaps) {
    const rect = tileRect(tile, area);
    const near = (a, b) => Math.abs(a - b) <= 1;
    const side = (name, onEdge) => onEdge ? gaps.outer[name] : gaps.inner[name] / 2;
    const left = side('left', near(rect.x, area.x));
    const top = side('top', near(rect.y, area.y));
    const right = side('right', near(rect.x + rect.width, area.x + area.width));
    const bottom = side('bottom', near(rect.y + rect.height, area.y + area.height));
    const frame = {
        x: Math.trunc(rect.x + left),
        y: Math.trunc(rect.y + top),
        width: Math.trunc(rect.width - left - right),
        height: Math.trunc(rect.height - top - bottom),
    };
    return frame.width > 0 && frame.height > 0 ? frame : null;
}

/**
 * Where a tiled window goes in the new area, or null if it's there already.
 *
 * @param {{x: number, y: number, width: number, height: number}} frame - the window now
 * @param {{x: number, y: number, width: number, height: number}} tile
 * @param {{x: number, y: number, width: number, height: number}} area
 * @param {{inner: object, outer: object}} gaps
 * @returns {{x: number, y: number, width: number, height: number}|null}
 */
export function refitFrame(frame, tile, area, gaps) {
    const to = tiledFrame(tile, area, gaps);
    if (!to)
        return null;
    if (to.x === frame.x && to.y === frame.y && to.width === frame.width && to.height === frame.height)
        return null;
    return to;
}

/**
 * Whether two areas differ.
 *
 * @param {{x: number, y: number, width: number, height: number}|undefined} a
 * @param {{x: number, y: number, width: number, height: number}|undefined} b
 * @returns {boolean}
 */
export function areaChanged(a, b) {
    if (!a || !b)
        return false;
    return a.x !== b.x || a.y !== b.y || a.width !== b.width || a.height !== b.height;
}

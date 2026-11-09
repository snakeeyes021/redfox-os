// SPDX-License-Identifier: Apache-2.0
//
// How a position on the brightness slider splits into backlight and software
// dim. Kept free of Shell imports so tests can run it under plain gjs.
//
//   slider  0 ............ range ...................... 1
//   backlight  (minimum)     |  minimum -----> maximum
//   picture    floor --> 1   |  1

export function backlightFor(value, range) {
    return value <= range ? 0 : (value - range) / (1 - range);
}

export function levelFor(value, range, floor) {
    return value >= range ? 1 : floor + (1 - floor) * (value / range);
}

// The slider position for a backlight changed by something other than the
// slider. The picture isn't dimmed at any such position.
export function valueForBacklight(backlight, range) {
    return range + backlight * (1 - range);
}

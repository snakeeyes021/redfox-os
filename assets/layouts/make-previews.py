#!/usr/bin/python3
"""Draw small vector previews of RedFox's desktop layouts, for a layout picker.

    python3 assets/layouts/make-previews.py

Writes assets/layouts/<layout id>.svg, one per layout in redfox-layout.
Each is a sketch, not a screenshot: wallpaper, bars, dock and one window,
in the places that layout puts them.
"""
import os

W, H = 240, 150
HERE = os.path.dirname(os.path.abspath(__file__))

BAR = "#3d3d40"
WINDOW = "#fbfbfb"
HEADER = "#ececec"
RED = "#b22234"
APP_COLOURS = ["#3584e4", "#f6a33a", "#e66161", "#9141ac", "#26a269", "#62a0ea"]


def wallpaper():
    # A pale version of the ink wallpaper: soft blobs on light grey.
    blobs = [(70, 70, 46, "#f4a6a0"), (120, 60, 40, "#f2a9cf"), (168, 72, 44, "#8fd3f4"),
             (198, 92, 34, "#9be7d8"), (95, 105, 38, "#f9c9b8")]
    out = [f'<rect width="{W}" height="{H}" fill="#e9e9eb"/>',
           '<g filter="url(#soft)" opacity="0.75">']
    out += [f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>' for x, y, r, c in blobs]
    out.append("</g>")
    return out


def top_bar():
    return [f'<rect width="{W}" height="9" fill="{BAR}"/>',
            '<rect x="4" y="2.5" width="10" height="4" rx="2" fill="#ffffff" opacity="0.85"/>',
            f'<rect x="{W / 2 - 12}" y="3" width="24" height="3" rx="1.5" fill="#ffffff" opacity="0.85"/>',
            *[f'<circle cx="{W - 6 - 6 * i}" cy="4.5" r="1.6" fill="#ffffff" opacity="0.85"/>' for i in range(3)]]


def app_icons(positions, size):
    return [f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{size / 4}" fill="{APP_COLOURS[i % len(APP_COLOURS)]}"/>'
            for i, (x, y) in enumerate(positions)]


def window(x, y, w, h, buttons="right"):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{WINDOW}" filter="url(#shadow)"/>',
           f'<path d="M{x} {y + 4} a4 4 0 0 1 4 -4 h{w - 8} a4 4 0 0 1 4 4 v6 h-{w} z" fill="{HEADER}"/>']
    if buttons == "right":
        out += [f'<circle cx="{x + w - 5 - 5 * i}" cy="{y + 5}" r="1.5" fill="#9a9a9a"/>' for i in range(3)]
    elif buttons == "left":
        out += [f'<circle cx="{x + 5 + 5 * i}" cy="{y + 5}" r="1.5" fill="#9a9a9a"/>' for i in range(3)]
    elif buttons == "close-left":
        out.append(f'<circle cx="{x + 5}" cy="{y + 5}" r="1.6" fill="#9a9a9a"/>')
    # a few lines of content
    out += [f'<rect x="{x + 8}" y="{y + 16 + 7 * i}" width="{w * (0.7 - 0.12 * i)}" height="3" rx="1.5" fill="#dcdcdc"/>'
            for i in range(4)]
    return out


def start_button(x, y, size):
    # The swirl, reduced to a red disc with a light curl.
    r = size / 2
    return [f'<circle cx="{x + r}" cy="{y + r}" r="{r}" fill="{RED}"/>',
            f'<path d="M{x + r} {y + r * 0.45} a{r * 0.55} {r * 0.55} 0 1 1 -{r * 0.5} {r * 0.75}" '
            f'fill="none" stroke="#fff" stroke-width="{size / 8}" stroke-linecap="round"/>']


def tiling_button(x, y, size):
    return [f'<rect x="{x}" y="{y}" width="{size * 0.42}" height="{size}" rx="1" fill="#ffffff" opacity="0.9"/>',
            f'<rect x="{x + size * 0.52}" y="{y}" width="{size * 0.48}" height="{size * 0.45}" rx="1" fill="#ffffff" opacity="0.9"/>',
            f'<rect x="{x + size * 0.52}" y="{y + size * 0.55}" width="{size * 0.48}" height="{size * 0.45}" rx="1" fill="#ffffff" opacity="0.9"/>']


def taskbar(centred):
    h, icon = 14, 9
    y = H - h
    out = [f'<rect y="{y}" width="{W}" height="{h}" fill="{BAR}"/>']
    n = 5
    group = (2 + n) * (icon + 4)
    x0 = (W - group) / 2 if centred else 4
    iy = y + (h - icon) / 2
    out += start_button(x0, iy, icon)
    out += tiling_button(x0 + icon + 4, iy + 1, icon - 2)
    out += app_icons([(x0 + (icon + 4) * (i + 2), iy) for i in range(n)], icon)
    # tray, status icons, then the clock, then the show-desktop sliver
    out += [f'<circle cx="{W - 46 + 5 * i}" cy="{y + h / 2}" r="1.6" fill="#ffffff" opacity="0.85"/>' for i in range(3)]
    out.append(f'<rect x="{W - 28}" y="{y + h / 2 - 1.5}" width="20" height="3" rx="1.5" fill="#ffffff" opacity="0.85"/>')
    return out


def side_dock(floating):
    icon, n = 9, 6
    if floating:
        x, y, w, h = 4, 34, 15, n * (icon + 4) + 8
        out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{BAR}" opacity="0.92"/>']
    else:
        x, y, w, h = 0, 9, 15, H - 9
        out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{BAR}"/>']
    out += app_icons([(x + 3, y + 5 + (icon + 4) * i) for i in range(n)], icon)
    # the app grid button at the bottom
    gy = y + h - 9 if not floating else y + h - 6
    out += [f'<circle cx="{x + 4.5 + 3 * (i % 3)}" cy="{gy - 3 * (i // 3)}" r="0.8" fill="#fff"/>' for i in range(9)] if not floating else []
    return out


def bottom_dock():
    icon, n = 10, 7
    w = n * (icon + 4) + 6
    x, y = (W - w) / 2, H - icon - 12
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{icon + 8}" rx="5" fill="{BAR}" opacity="0.92"/>']
    out += app_icons([(x + 5 + (icon + 4) * i, y + 4) for i in range(n)], icon)
    return out


def overview_dash_hint():
    # GNOME's layout has no dock; the dash appears in the overview only.
    return [f'<rect x="{W / 2 - 34}" y="{H - 16}" width="68" height="11" rx="5" fill="{BAR}" opacity="0.25" '
            'stroke="#3d3d40" stroke-dasharray="2 2" stroke-width="0.8"/>']


LAYOUTS = {
    "gnome": lambda: [*top_bar(), *window(48, 30, 144, 86), *overview_dash_hint()],
    "ubuntu": lambda: [*top_bar(), *side_dock(False), *window(56, 28, 140, 88)],
    "macos": lambda: [*top_bar(), *window(48, 22, 144, 84, "left"), *bottom_dock()],
    "windows-classic": lambda: [*window(46, 18, 148, 92), *taskbar(False)],
    "windows": lambda: [*window(46, 18, 148, 92), *taskbar(True)],
    "redfox": lambda: [*top_bar(), *side_dock(True), *window(56, 28, 140, 88, "close-left")],
}

DEFS = """<defs>
<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9"/></filter>
<filter id="shadow" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="1.5" stdDeviation="2" flood-opacity="0.25"/></filter>
<clipPath id="screen"><rect width="240" height="150" rx="6"/></clipPath>
</defs>"""


def svg(parts):
    body = "\n".join(parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
            f'{DEFS}\n<g clip-path="url(#screen)">\n{body}\n</g>\n</svg>\n')


def main():
    for layout, draw in LAYOUTS.items():
        with open(os.path.join(HERE, f"{layout}.svg"), "w") as f:
            f.write(svg([*wallpaper(), *draw()]))
        print(f"wrote assets/layouts/{layout}.svg")


if __name__ == "__main__":
    main()

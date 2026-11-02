#!/usr/bin/env python3
"""Generate RedFoxOS's drawn marks (no source art; drawn here in code):

  - the terminal fox: a simplified nine-tailed fox for fastfetch, in RedFox reds,
    written as truecolour half-block text  -> files/system/usr/share/ublue-os/bazzite/logo.txt
  - the swirl: three swirling tails with fox ears, one colour, for symbolic icons
    (ArcMenu's start button, panel and menu icons) -> redfox-logo-symbolic.svg

Run from the repository root after changing a drawing:

    python3 assets/branding/make-marks.py

Both are stand-ins until the commissioned artwork arrives (see docs/branding.md).
"""
import math
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brush import Canvas, bez, chain, curl, stroke  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "files" / "system"

RED, DEEP, WHITE, INK = (178, 34, 52), (122, 16, 34), (244, 236, 236), (60, 10, 20)
SCALE = 12            # canvas units -> pixels when rasterising
# 34 columns gives 20 rows: small enough to sit beside fastfetch's info in a
# default 80x24 terminal (a logo taller than the window scrolls, and fastfetch
# then draws the info over it).
TERMINAL_COLUMNS = 34


# --- The terminal fox -------------------------------------------------------

# Tails come in three kinds, so the fan isn't nine copies of one shape. (Small
# tight curls read as blobs with a hole at terminal size, so there are none.)
#   bushy: full and soft, tapering to a point; some with a white tip
#   swirl: slimmer, ending in a wide open spiral
#   hook:  medium, ending in a loose half-curl
TAILS = [  # (control 1, control 2, end, curl side, kind, colour)
    ((46, 66), (54, 26), (40, 6), -1, "swirl", RED),
    ((50, 72), (52, 48), (60, 30), 1, "bushy", DEEP),
    ((30, 64), (48, 32), (20, 14), -1, "wave", RED),
    ((40, 76), (26, 52), (26, 36), -1, "bushy", DEEP),
    ((28, 70), (26, 40), (6, 36), -1, "wave", DEEP),
    ((38, 80), (12, 72), (2, 62), 1, "bushy-white", RED),
    ((30, 98), (22, 70), (4, 82), 1, "wave", DEEP),
    ((44, 96), (22, 112), (8, 104), 1, "bushy", RED),
    ((52, 112), (34, 98), (24, 112), 1, "wave", DEEP),
]


def tail(c, start, c1, c2, end, side, kind, col):
    path = bez(start, c1, c2, end)
    if kind.startswith("bushy"):
        # full, with a soft rounded end rather than a point
        c.poly(stroke(path, 4, 7, wmid=15, ease=1.0), col)
        c.ellipse(end[0], end[1], 3.5, 3.5, col)
        if kind.endswith("white"):  # the end white, like a fox's tail tip
            n = len(path)
            c.poly(stroke(path[int(n * 0.78):], 10, 7, ease=1.0), WHITE)
            c.ellipse(end[0], end[1], 3.5, 3.5, WHITE)
    elif kind == "swirl":
        c.poly(stroke(curl(path, 8, turns=1.1, side=side, shrink=0.4), 4, 1.6, wmid=10, ease=0.8), col)
    else:  # wave: an S-curve that tapers to a fine flick
        c.poly(stroke(path, 4, 0.5, wmid=11, ease=1.2), col)


def draw_fox(c, face=True):
    """Sitting, turned toward the viewer, nine tails fanned behind (after the
    painting). face=False leaves out the eyes and nose, which the terminal version
    places pixel by pixel so they stay crisp."""
    base = (54, 90)
    for c1, c2, end, side, kind, col in TAILS:
        tail(c, base, c1, c2, end, side, kind, col)
    body = chain(bez((66, 30), (60, 44), (54, 60), (52, 82)), bez((52, 82), (50, 96), (56, 102), (64, 102)),
                 bez((64, 102), (74, 102), (84, 102), (92, 102)), bez((92, 102), (90, 80), (94, 56), (88, 40)),
                 bez((88, 40), (84, 34), (74, 30), (66, 30)))
    c.poly(body, RED)
    c.poly(chain(bez((66, 30), (60, 44), (54, 60), (52, 82)), bez((52, 82), (50, 94), (56, 100), (62, 100)),
                 bez((62, 100), (64, 92), (62, 80), (60, 72)), bez((60, 72), (60, 58), (64, 44), (68, 32))), DEEP)
    c.poly(chain(bez((70, 36), (78, 38), (88, 40), (90, 48)), bez((90, 48), (92, 58), (88, 66), (82, 72)),
                 bez((82, 72), (76, 64), (72, 50), (70, 36))), WHITE)
    c.poly(stroke(bez((79, 72), (79, 82), (79, 94), (79, 100)), 1.8, 1.8), DEEP)
    c.poly([(70, 97), (78, 97), (78, 102), (69, 102)], WHITE)
    c.poly([(80, 97), (89, 97), (91, 102), (80, 102)], WHITE)
    c.poly(stroke(curl(bez((58, 90), (57, 82), (64, 80), (66, 86)), 3.4, turns=0.9, side=1), 2.6, 1.0), WHITE)
    head = chain(bez((60, 22), (66, 11), (82, 9), (94, 15)), bez((94, 15), (99, 20), (98, 27), (93, 33)),
                 bez((93, 33), (90, 38), (87, 43), (84, 46)), bez((84, 46), (74, 42), (62, 34), (60, 22)))
    c.poly(head, RED)
    c.poly([(61, 24), (57, 0), (73, 12)], RED)
    c.poly([(80, 10), (93, 0), (95, 18)], RED)
    c.poly([(61.5, 18), (59.5, 5), (68, 12)], INK)
    c.poly([(83, 11), (91, 4), (92, 15)], INK)
    c.poly(chain(bez((60, 21), (66, 26), (72, 27), (77, 30)), bez((77, 30), (80, 34), (82, 40), (84, 46)),
                 bez((84, 46), (74, 42), (62, 34), (60, 21))), WHITE)
    c.poly(chain(bez((88, 30), (92, 27), (96, 25), (98, 24)), bez((98, 24), (97, 30), (91, 38), (85, 45)),
                 bez((85, 45), (86, 40), (87, 34), (88, 30))), WHITE)
    if face:
        c.poly([(68, 19), (76, 20.5), (71, 24)], INK)
        c.poly([(84, 20.5), (91, 19), (89, 23.5)], INK)
        c.poly([(81, 41), (88, 40), (84.5, 46.5)], INK)


# Pixel features for the terminal: (centre in canvas units, mirrored, pixel offsets).
# Narrow slits whose outer corners lift, like the drawing's eyes, and a solid nose,
# all one dark colour (blending them in made the fox look startled).
EYE = [(-1, -1), (0, 0), (1, 0)]
NOSE = [(-1, 0), (0, 0)]
TERMINAL_FEATURES = [((72.5, 21), False, EYE), ((87, 21), True, EYE), ((85, 42.5), False, NOSE)]


def nearest(p):
    if p[3] < 110:
        return None
    return min((RED, DEEP, WHITE, INK), key=lambda q: sum((a - b) ** 2 for a, b in zip(q, p[:3])))


def terminal_art(cols):
    c = Canvas(100, 116, SCALE)
    draw_fox(c, face=False)
    im = c.im
    bx0, by0, bx1, by1 = im.getchannel("A").getbbox()
    im = im.crop((bx0, by0, bx1, by1))
    rows_px = round(im.height * cols / im.width)
    rows_px += rows_px % 2
    small = im.resize((cols, rows_px), Image.LANCZOS).load()
    grid = [[nearest(small[x, y]) for x in range(cols)] for y in range(rows_px)]
    for (X, Y), mirror, pixels in TERMINAL_FEATURES:
        gx = round((X * SCALE - bx0) * cols / (bx1 - bx0))
        gy = round((Y * SCALE - by0) * rows_px / (by1 - by0))
        for dx, dy in pixels:
            grid[gy + dy][gx + (-dx if mirror else dx)] = INK
    # Two pixels per character cell: the upper half block takes the top pixel's
    # colour as foreground and the bottom pixel's as background.
    lines = []
    for y in range(0, rows_px, 2):
        line, state = "", None
        for x in range(cols):
            top, bottom = grid[y][x], grid[y + 1][x]
            if top is None and bottom is None:
                want, ch = "\x1b[0m", " "
            elif bottom is None:
                want, ch = "\x1b[0;38;2;%d;%d;%dm" % top, "▀"
            elif top is None:
                want, ch = "\x1b[0;38;2;%d;%d;%dm" % bottom, "▄"
            elif top == bottom:
                want, ch = "\x1b[0;38;2;%d;%d;%dm" % top, "█"
            else:
                want, ch = "\x1b[0;38;2;%d;%d;%d;48;2;%d;%d;%dm" % (top + bottom), "▀"
            if want != state:
                line += want
                state = want
            line += ch
        lines.append(line + "\x1b[0m")
    blank = lambda line: line.replace("\x1b[0m", "").strip() == ""
    while lines and blank(lines[0]):
        lines.pop(0)
    while lines and blank(lines[-1]):
        lines.pop()
    return lines


# --- The swirl (symbolic) ---------------------------------------------------

def draw_swirl(c, col):
    """Three tails swirling round a centre, with two fox ears on top."""
    cx, cy = 50, 58
    for k in range(3):
        a0 = math.radians(90 + k * 120)
        pts = []
        for i in range(70):
            f = i / 69
            r = 5 + 33 * f
            a = a0 + f * math.radians(210)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        c.poly(stroke(pts, 2, 1.0, wmid=15, ease=1.3), col)
    c.poly([(26, 36), (22, 2), (46, 24)], col)
    c.poly([(74, 36), (78, 2), (54, 24)], col)


def swirl_svg(fill):
    c = Canvas(100, 100, SCALE)
    draw_swirl(c, (0, 0, 0))
    paths = "".join(item.replace('fill="#000000"', f'fill="{fill}"') for item in c.svg)
    # Square, so it sits centred wherever a square icon is expected.
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="1 0 98 98">'
            f'{paths}</svg>\n')


def save_text(text, relpath):
    path = SYSTEM / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    print(relpath)


def main():
    lines = terminal_art(TERMINAL_COLUMNS)
    save_text("\n".join(lines) + "\n", "usr/share/ublue-os/bazzite/logo.txt")
    print(f"  {TERMINAL_COLUMNS} columns x {len(lines)} rows (set these in fastfetch.jsonc)")
    # Symbolic icons are recoloured by GTK and GNOME Shell; the fill is only the default.
    save_text(swirl_svg("#2e3436"), "usr/share/icons/hicolor/scalable/apps/redfox-logo-symbolic.svg")
    # Reference renders for the artist brief.
    c = Canvas(100, 116, SCALE)
    draw_fox(c)
    c.im.save(ROOT / "assets" / "branding" / "terminal-fox.png", optimize=True)
    s = Canvas(100, 100, SCALE)
    draw_swirl(s, (178, 34, 52))
    s.im.save(ROOT / "assets" / "branding" / "swirl.png", optimize=True)


if __name__ == "__main__":
    main()

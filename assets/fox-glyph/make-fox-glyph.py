#!/usr/bin/env python3
"""Builds RedFox Symbols, a one-glyph font: RedFox's fox face as a symbol
at U+10F000 (a private-use codepoint), so a terminal prompt can show it in
the prompt's own colours, like Nerd Font symbols. It's about one terminal
cell wide.

Writes files/system/usr/share/fonts/redfox-symbols/RedFoxSymbols.ttf and,
for reference, assets/fox-glyph/fox-face.svg.

Needs fontTools and shapely (pip install fonttools shapely), so it isn't
run at image build time: run it after changing the shape and commit both
files. Usage (from the repository root): python3 assets/fox-glyph/make-fox-glyph.py
"""
import os

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT = os.path.join(ROOT, "files", "system", "usr", "share", "fonts", "redfox-symbols",
                    "RedFoxSymbols.ttf")
SVG = os.path.join(ROOT, "assets", "fox-glyph", "fox-face.svg")
CODEPOINT = 0x10F000

# The fox face, drawn on a 100 x 100 grid (y down): the head, then what's
# cut out of it (inner ears, eyes, the muzzle line and the nose).
HEAD = [(16, 2), (40, 28), (60, 28), (84, 2), (86, 40), (98, 58), (50, 94), (2, 58), (14, 40)]
EARS = [[(21, 10), (36, 28), (19, 35)], [(79, 10), (64, 28), (81, 35)]]
EYES = [[(25, 44), (41, 49), (29, 51)], [(75, 44), (59, 49), (71, 51)]]
NOSE = [(43, 86), (57, 86), (50, 94)]
MUZZLE = [(22, 52), (38, 60), (50, 80), (62, 60), (78, 52)]

# Font metrics: 1000 units per em; the glyph is about one cell (0.6 em) wide.
UPM, ASC, DESC = 1000, 880, -120
ADVANCE, MAX_W, MAX_H, TOP = 600, 640, 780, 790


def fox():
    cuts = [Polygon(p) for p in EARS + EYES + [NOSE]]
    cuts.append(LineString(MUZZLE).buffer(2.4, join_style=2, cap_style=2))
    return Polygon(HEAD).difference(unary_union(cuts))


def polygons(geom):
    return list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]


def signed_area(points):
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1])) / 2


def main():
    geom = fox()
    x1, y1, x2, y2 = geom.bounds

    paths = []
    for p in polygons(geom):
        for ring in [p.exterior, *p.interiors]:
            paths.append("M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in list(ring.coords)[:-1]) + " Z")
    with open(SVG, "w", encoding="utf-8") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x1 - 4:.1f} {y1 - 4:.1f} '
                f'{x2 - x1 + 8:.1f} {y2 - y1 + 8:.1f}"><path fill="currentColor" fill-rule="evenodd" '
                f'd="{" ".join(paths)}"/></svg>\n')

    scale = min(MAX_W / (x2 - x1), MAX_H / (y2 - y1))
    ox = (ADVANCE - (x2 - x1) * scale) / 2
    oy = (MAX_H - (y2 - y1) * scale) / 2
    pen = TTGlyphPen(None)
    for p in polygons(geom):
        for i, ring in enumerate([p.exterior, *p.interiors]):
            pts = [(round(ox + (x - x1) * scale), round(TOP - oy - (y - y1) * scale))
                   for x, y in list(ring.coords)[:-1]]
            # TrueType: outer contours clockwise, holes counter-clockwise (y up).
            if (i == 0) != (signed_area(pts) < 0):
                pts.reverse()
            pen.moveTo(pts[0])
            for pt in pts[1:]:
                pen.lineTo(pt)
            pen.closePath()
    glyphs = {".notdef": TTGlyphPen(None).glyph(), "space": TTGlyphPen(None).glyph(),
              "fox": pen.glyph()}

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder([".notdef", "space", "fox"])
    fb.setupCharacterMap({0x20: "space", CODEPOINT: "fox"})
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({".notdef": (ADVANCE, 0), "space": (ADVANCE, 0), "fox": (ADVANCE, 0)})
    fb.setupHorizontalHeader(ascent=ASC, descent=DESC)
    fb.setupNameTable({"familyName": "RedFox Symbols", "styleName": "Regular",
                       "copyright": "RedFox Labs", "version": "Version 1.0"})
    fb.setupOS2(sTypoAscender=ASC, sTypoDescender=DESC, usWinAscent=ASC, usWinDescent=-DESC)
    fb.setupPost()
    os.makedirs(os.path.dirname(FONT), exist_ok=True)
    fb.save(FONT)
    print(f"wrote {FONT} (U+{CODEPOINT:X}) and {SVG}")


if __name__ == "__main__":
    main()

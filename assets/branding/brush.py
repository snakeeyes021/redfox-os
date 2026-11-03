"""Small vector kit for the RedFox marks: tapered brush strokes along curves that end in curls."""
import math
from PIL import Image, ImageDraw

def bez(p0, p1, p2, p3, n=60):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                    u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return out

def curl(path, r0, turns=1.1, side=1, shrink=0.25, n=80):
    """Continue a path into a spiral curling to one side (side=+1 left of travel, -1 right)."""
    (x1, y1), (x2, y2) = path[-2], path[-1]
    dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy) or 1; dx, dy = dx / L, dy / L
    nx, ny = -dy * side, dx * side           # normal toward the curl
    # screen coords have y down, so "left of travel" flips; side just picks one
    cx, cy = x2 + nx * r0, y2 + ny * r0
    a0 = math.atan2(y2 - cy, x2 - cx)
    # direction of rotation that continues the travel direction
    tx, ty = -(y2 - cy), (x2 - cx)            # tangent for increasing angle
    sgn = 1 if tx * dx + ty * dy > 0 else -1
    pts = []
    for i in range(1, n + 1):
        f = i / n
        a = a0 + sgn * f * turns * 2 * math.pi
        r = r0 * (1 - (1 - shrink) * f)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return path + pts

def stroke(path, w0, w1, wmid=None, ease=1.0):
    """Polygon for a stroke whose width goes w0 -> (wmid) -> w1 along the path."""
    # cumulative length
    d = [0.0]
    for (a, b), (c, e) in zip(path, path[1:]):
        d.append(d[-1] + math.hypot(c - a, e - b))
    total = d[-1] or 1
    left, right = [], []
    for i, (x, y) in enumerate(path):
        t = d[i] / total
        if wmid is None:
            w = w0 + (w1 - w0) * (t ** ease)
        else:
            w = (w0 + (wmid - w0) * (t / 0.35)) if t < 0.35 else (wmid + (w1 - wmid) * (((t - 0.35) / 0.65) ** ease))
        j0, j1 = max(0, i - 1), min(len(path) - 1, i + 1)
        dx, dy = path[j1][0] - path[j0][0], path[j1][1] - path[j0][1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        left.append((x + nx * w / 2, y + ny * w / 2))
        right.append((x - nx * w / 2, y - ny * w / 2))
    return left + right[::-1]

class Canvas:
    def __init__(self, w, h, scale=10):
        self.w, self.h, self.s = w, h, scale
        self.im = Image.new("RGBA", (round(w * scale), round(h * scale)), (0, 0, 0, 0))
        self.dr = ImageDraw.Draw(self.im)
        self.svg = []
    def poly(self, pts, col):
        fill = (0, 0, 0, 0) if col is None else (col + (255,) if len(col) == 3 else col)
        self.dr.polygon([(x * self.s, y * self.s) for x, y in pts], fill=fill)
        if col is not None:
            self.svg.append('<path d="M%s Z" fill="#%02x%02x%02x"/>' % (" L".join("%.2f,%.2f" % p for p in pts), *col[:3]))
        else:
            self.svg.append(('CUT', pts))
    def ellipse(self, cx, cy, rx, ry, col, n=40):
        self.poly([(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)], col)
    def save_svg(self, path, pad=2):
        body, cuts = [], []
        for item in self.svg:
            if isinstance(item, tuple): cuts.append(item[1])
            else: body.append(item)
        vb = f"{-pad} {-pad} {self.w + 2*pad} {self.h + 2*pad}"
        if cuts:
            cut = "".join('<path d="M%s Z" fill="black"/>' % " L".join("%.2f,%.2f" % p for p in c) for c in cuts)
            inner = "".join(b.replace('fill="#', 'fill="#') for b in body)
            s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}"><mask id="m" maskUnits="userSpaceOnUse">'
                 f'<rect x="{-pad}" y="{-pad}" width="{self.w+2*pad}" height="{self.h+2*pad}" fill="white"/>{cut}</mask>'
                 f'<g mask="url(#m)">{inner}</g></svg>\n')
        else:
            s = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">{"".join(body)}</svg>\n'
        open(path, "w").write(s)
    def at(self, size_h):
        """Downscaled copy whose height is size_h."""
        w = round(self.im.width * size_h / self.im.height)
        return self.im.resize((w, size_h), Image.LANCZOS)

def stroke_fn(path, wfn):
    """Polygon for a stroke whose width at fraction t of its length is wfn(t)."""
    d = [0.0]
    for (a, b), (c, e) in zip(path, path[1:]):
        d.append(d[-1] + math.hypot(c - a, e - b))
    total = d[-1] or 1
    left, right = [], []
    for i, (x, y) in enumerate(path):
        w = max(0.0, wfn(d[i] / total))
        j0, j1 = max(0, i - 1), min(len(path) - 1, i + 1)
        dx, dy = path[j1][0] - path[j0][0], path[j1][1] - path[j0][1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        left.append((x + nx * w / 2, y + ny * w / 2)); right.append((x - nx * w / 2, y - ny * w / 2))
    return left + right[::-1]

def chain(*segs):
    out = []
    for s in segs:
        out += s if not out else s[1:]
    return out

def brushw(peak, at=0.4, start=1.5, end=0.0, p=1.6):
    """Brush width: swells from start to peak at `at`, then tapers to end."""
    def f(t):
        if t < at:
            return start + (peak - start) * math.sin(t / at * math.pi / 2)
        u = (t - at) / (1 - at)
        return end + (peak - end) * (1 - u ** p)
    return f

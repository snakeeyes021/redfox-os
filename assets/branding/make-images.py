#!/usr/bin/env python3
"""Generate RedFoxOS's logos, icons, login and boot images from the source art.

Run from the repository root after changing the source art:

    python3 assets/branding/make-images.py

Sources (no new artwork is drawn here; everything is cropped, scaled,
padded or recoloured from these):
  assets/red_fox_labs_logo_2_semi-transparent.png  the nine-tailed fox, white-filled
  assets/branding/wordmark-source.png               fox + "RedFoxOS" wordmark (cut from
                                                    updatelogo.png, minus a 3 px edge line
                                                    it had on the right)

Outputs go straight into files/system/, where the image build picks them up.
"""

import base64
import io
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "files" / "system"
FOX_SOURCE = ROOT / "assets" / "red_fox_labs_logo_2_semi-transparent.png"
WORDMARK_SOURCE = ROOT / "assets" / "branding" / "wordmark-source.png"

# In wordmark-source.png the fox ends and the lettering starts at about
# this fraction of the trimmed width.
TEXT_START = 0.345

# Light lettering for dark backgrounds (GDM, the boot screen, dark mode).
LIGHT_TEXT = (244, 236, 236)


def trimmed(im, threshold=24):
    """Crop to the pixels that are more than faintly visible."""
    alpha = im.getchannel("A").point(lambda a: 255 if a > threshold else 0)
    box = alpha.getbbox()
    return im.crop(box) if box else im


def fit(im, width=None, height=None):
    w, h = im.size
    if width and height:
        scale = min(width / w, height / h)
    elif width:
        scale = width / w
    else:
        scale = height / h
    return im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)


def on_canvas(im, size, margin=0.0):
    """Centre im on a transparent canvas of size, leaving a margin fraction."""
    cw, ch = size
    inner = fit(im, width=cw * (1 - 2 * margin), height=ch * (1 - 2 * margin))
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.alpha_composite(inner, ((cw - inner.width) // 2, (ch - inner.height) // 2))
    return canvas


def recolour(im, rgb):
    """Same shape and alpha, new colour (keeps a little of the ink shading)."""
    out = Image.new("RGBA", im.size)
    src = im.load()
    dst = out.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = src[x, y]
            shade = 0.88 + 0.12 * ((r + g + b) / 765)
            dst[x, y] = (round(rgb[0] * shade), round(rgb[1] * shade), round(rgb[2] * shade), a)
    return out


def split_wordmark():
    full = trimmed(Image.open(WORDMARK_SOURCE).convert("RGBA"))
    cut = round(full.width * TEXT_START)
    return trimmed(full.crop((0, 0, cut, full.height))), trimmed(full.crop((cut, 0, full.width, full.height)))


def lockup(fox, text, height, gap=0.06):
    """Fox beside the wordmark, as in the original artwork."""
    fox = fit(fox, height=height)
    text = fit(text, height=round(height * 0.5))
    gap_px = round(height * gap)
    canvas = Image.new("RGBA", (fox.width + gap_px + text.width, height), (0, 0, 0, 0))
    canvas.alpha_composite(fox, (0, 0))
    canvas.alpha_composite(text, (fox.width + gap_px, round(height * 0.52 - text.height / 2)))
    return canvas


def save(im, relpath):
    path = SYSTEM / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, optimize=True)
    print(f"{relpath}  {im.width}x{im.height}")


def save_svg_wrapper(im, relpath):
    """A scalable icon that keeps the image's aspect ratio (GTK fits plain
    PNG icons into a square)."""
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    data = base64.b64encode(buf.getvalue()).decode()
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
           f'width="{im.width}" height="{im.height}" viewBox="0 0 {im.width} {im.height}">'
           f'<image width="{im.width}" height="{im.height}" '
           f'xlink:href="data:image/png;base64,{data}"/></svg>\n')
    path = SYSTEM / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg)
    print(f"{relpath}  {im.width}x{im.height} (svg)")


def main():
    fox = trimmed(Image.open(FOX_SOURCE).convert("RGBA"))
    _, text_dark = split_wordmark()
    text_light = recolour(text_dark, LIGHT_TEXT)

    # The app/OS icon (os-release LOGO=redfox-logo): the fox on a square.
    for size in (16, 22, 24, 32, 48, 64, 96, 128, 256, 512):
        save(on_canvas(fox, (size, size), margin=0.02 if size < 48 else 0.04),
             f"usr/share/icons/hicolor/{size}x{size}/apps/redfox-logo.png")

    # Settings > About: fox + wordmark, dark lettering and light lettering.
    save_svg_wrapper(lockup(fox, text_dark, 320), "usr/share/icons/hicolor/scalable/apps/redfox-logo-text.svg")
    save_svg_wrapper(lockup(fox, text_light, 320), "usr/share/icons/hicolor/scalable/apps/redfox-logo-text-dark.svg")

    # GDM login screen (dark background), drawn at its natural size.
    save(lockup(fox, text_light, 104), "usr/share/pixmaps/fedora-gdm-logo.png")
    # Boot splash watermark (black background), bottom centre.
    save(lockup(fox, text_light, 120), "usr/share/plymouth/themes/spinner/watermark.png")

    # Fedora's logo files, which other software shows (installer, initial
    # setup, some About dialogs). Same sizes as Fedora's, RedFox art.
    save(on_canvas(lockup(fox, text_dark, 400), (521, 164)), "usr/share/pixmaps/fedora-logo.png")
    save(on_canvas(lockup(fox, text_dark, 400), (279, 80)), "usr/share/pixmaps/fedora_logo_med.png")
    save(on_canvas(lockup(fox, text_dark, 400), (150, 47)), "usr/share/pixmaps/fedora-logo-small.png")
    save(on_canvas(lockup(fox, text_light, 400), (279, 80)), "usr/share/pixmaps/fedora_whitelogo_med.png")
    save(on_canvas(fox, (128, 128), margin=0.04), "usr/share/pixmaps/fedora-logo-sprite.png")
    save(on_canvas(fox, (252, 252), margin=0.04), "usr/share/pixmaps/system-logo-white.png")
    save_svg_wrapper(lockup(fox, text_light, 240), "usr/share/pixmaps/fedora_whitelogo.svg")
    save_svg_wrapper(on_canvas(fox, (256, 256), margin=0.04), "usr/share/pixmaps/fedora-logo-sprite.svg")


if __name__ == "__main__":
    main()

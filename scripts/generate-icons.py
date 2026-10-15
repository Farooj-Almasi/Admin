"""
Generate the admin panel's PWA icons from the brand badge.

Run: python3 scripts/generate-icons.py  (needs Pillow)

The brand mark is a round badge (rooster + wordmark banner) on its own ground,
so unlike a wordmark it does not need a white plate or an "ADMIN" label to read
at icon size — the badge is already a self-contained, recognisable shape. Two
shapes are still emitted, and the difference matters:

- `icon-*.png`  — "any" purpose. The badge fills the square; the OS rounds the
  corners.
- `icon-maskable-*.png` — "maskable" purpose. Android and Chrome crop this to a
  circle or squircle, cutting up to ~20% off each edge, so the badge sits inside
  a centred safe zone on a full-bleed ground. Shipping only an "any" icon gets
  it letterboxed into a white pillbox on those surfaces.

The source (`public/logo.jpeg`) is treated as a full-bleed image: its ground is
NOT keyed to transparent, because the badge itself contains large white areas
(the bird, the ring text) that keying would punch holes in.
"""

import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(HERE, "..", "public")
WHITE = (255, 255, 255, 255)


def master():
    """The badge as a clean square, padded on white if it is not exactly square."""
    im = Image.open(os.path.join(PUBLIC, "logo.jpeg")).convert("RGBA")
    side = max(im.size)
    sq = Image.new("RGBA", (side, side), WHITE)
    sq.paste(im, ((side - im.width) // 2, (side - im.height) // 2), im)
    return sq


def build(size, maskable):
    """One icon. `maskable` keeps the badge inside the crop-safe centre (~80%)."""
    canvas = Image.new("RGBA", (size, size), WHITE)
    m = master()
    if maskable:
        s = int(size * 0.80)
        canvas.alpha_composite(m.resize((s, s), Image.LANCZOS), ((size - s) // 2, (size - s) // 2))
    else:
        canvas.alpha_composite(m.resize((size, size), Image.LANCZOS))
    return canvas


def main():
    outputs = [
        ("icon-192.png", 192, False),
        ("icon-512.png", 512, False),
        ("icon-maskable-192.png", 192, True),
        ("icon-maskable-512.png", 512, True),
        # iOS ignores the manifest and reads this for "Add to Home Screen".
        # It is never masked, so it uses the "any" art.
        ("apple-touch-icon.png", 180, False),
        ("favicon-32.png", 32, False),
    ]
    for name, size, maskable in outputs:
        path = os.path.join(PUBLIC, name)
        icon = build(size, maskable)
        # No alpha: these sit on their own ground, and a stray alpha channel is
        # what App Store Connect rejects elsewhere in this platform.
        icon.convert("RGB").save(path, "PNG")
        print(name, Image.open(path).size, Image.open(path).mode)


if __name__ == "__main__":
    main()

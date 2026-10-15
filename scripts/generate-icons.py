"""
Generate the admin panel's PWA icons.

Run: python3 scripts/generate-icons.py  (needs Pillow)

The panel is installed to a desktop or taskbar beside the customer app's icon,
so the icon's whole job is to be told apart from it at ~48px. That is why the
word ADMIN is the largest element and the wordmark is secondary: the wordmark
is a 4:1 lockup that becomes an unreadable smudge in a square at icon size, so
leaning on it for identification would produce two indistinguishable tiles.

Two shapes are emitted, and the difference matters:

- `icon-*.png`  — "any" purpose. Art fills the square; the OS rounds the corners.
- `icon-maskable-*.png` — "maskable" purpose. Android and Chrome crop this to a
  circle or squircle, cutting up to ~20% off each edge, so the art sits inside a
  centred safe zone on a full-bleed brand ground. Shipping only an "any" icon
  gets it letterboxed into a white pillbox on those surfaces.
"""

import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(HERE, "..", "public")

MAGENTA = (229, 23, 139)
WHITE = (255, 255, 255)

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def wordmark():
    """The supplied logo, its white JPEG ground made transparent and trimmed."""
    im = Image.open(os.path.join(PUBLIC, "logo.jpeg")).convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            if r >= 246 and g >= 246 and b >= 246:
                px[x, y] = (r, g, b, 0)
    return im.crop(im.getbbox())


def fitted_font(draw, text, target_w, start):
    """Largest bold size whose rendered width fits `target_w`."""
    size = start
    while size > 8:
        font = ImageFont.truetype(BOLD, size)
        if draw.textlength(text, font=font) <= target_w:
            return font
        size -= 2
    return ImageFont.truetype(BOLD, 8)


def build(size, maskable):
    """One icon. `maskable` keeps the art inside the crop-safe centre."""
    canvas = Image.new("RGBA", (size, size), MAGENTA + (255,))
    draw = ImageDraw.Draw(canvas)

    # Maskable art must survive a circular crop: keep to the middle ~62%.
    content = size * (0.62 if maskable else 0.82)
    left = (size - content) / 2

    mark = wordmark()
    mark_w = int(content)
    mark_h = max(1, round(mark.height * mark_w / mark.width))
    # The logo is drawn for a white ground; on magenta it needs its own plate.
    plate_pad = round(size * 0.025)
    plate_h = mark_h + plate_pad * 2
    plate_top = round(left + content * 0.10)
    plate = Image.new("RGBA", (mark_w, plate_h), WHITE + (255,))
    plate.alpha_composite(mark.resize((mark_w, mark_h), Image.LANCZOS), (0, plate_pad))
    rounded = Image.new("L", plate.size, 0)
    ImageDraw.Draw(rounded).rounded_rectangle(
        [0, 0, plate.size[0] - 1, plate.size[1] - 1], radius=round(size * 0.02), fill=255
    )
    canvas.paste(plate, (round(left), plate_top), rounded)

    # ADMIN is the element that does the identifying, so it takes the space.
    font = fitted_font(draw, "ADMIN", content, round(size * 0.5))
    bbox = draw.textbbox((0, 0), "ADMIN", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    ty = plate_top + plate_h + (left + content - (plate_top + plate_h) - th) / 2
    draw.text(((size - tw) / 2 - bbox[0], ty - bbox[1]), "ADMIN", font=font, fill=WHITE)

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
